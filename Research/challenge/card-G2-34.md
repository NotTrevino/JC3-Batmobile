# Assumption challenge — G2-34 (`Tether, airlift and winch carriers`)

Scope: the card (`GRAB_BACKLOG.md` "G2-34 · Tether, airlift and winch carriers"), its §12 row, the
MODLOG blocks `G2-34 … intended change` / `… done` (lines 10885–10972) and the card's outputs
`Research/JC3Grab/TETHER.md` (+ `TETHER.json`, `Tools/scripts/jc3tether.py`).

All tests below were run read-only. Nothing was launched, no archive was written, nothing under
`D:\Games` was touched, nothing committed. Inputs are the decoded grab (`E:\Modding\_JC3grab`,
the project's own `JC3_RAW`), `Research/JC3Grab/PARTS_TABLE.jsonl`, `INDEX.jsonl` and the archives
through the project's readers.

---

## VERDICT

**The mass half and the bay half are solid; the "who has a winch" half is a one-vehicle census
presented as the fleet, and the mass ratios convert a unit the same document declares unknown.**

| # | Assumption | Verdict |
|---|---|---|
| A1 | `RigidBody.mass` covers the fleet (232 entities) and the donor is 975 | **HOLDS** |
| A2 | The mass unit is UNKNOWN, "so every comparison is a ratio, never a conversion" | **WEAK** — the percentages that follow *are* conversions of a kg design value; the field is kg-plausible across five families but carries no unit |
| A3 | WLD-7's car is 6,000 (6.154× the donor) | **WEAK** — the project's own build is 4,000 kg; 6,000 is the `v0602` field value / "6 t class", not the car being built |
| A4 | The compound cargo-plane entity carries the plane's 40,000 **and** the tank's 25,000 | **HOLDS** — both match the standalone entities exactly |
| A5 | `CVehicleCargoBay`: 12 objects on 12 entities, 7 members, no capacity or mass limit | **HOLDS** |
| A6 | "Only the planes have bay interaction points; the boat **and the flatbed** carry the bay and its door effects" | **BROKEN** — the flatbed has the bay and nothing else: no door effects, no points |
| A7 | "No helicopter has a bay (0 of 23)" | **WEAK** — 39 distinct helicopter leaves exist; 23 are decoded, and the 16 undecoded (DLC, mm230 custom) cannot be searched with the project's reader |
| A8 | No tether/grapple tune exists, so strength is UNKNOWN | **HOLDS** — and it now survives a content scan of 751 tune/def/module files |
| A9 | `tether_tear`/`tether_yank` carry no force/distance/mass | **HOLDS** — six object keys, two empty events, nothing numeric |
| A10 | 67 part behaviours, none of them winch/rope/tow/reel; "nearest is `CargoBayDoor`" | **WEAK** — `TrainCargo` exists (15 rows, on the very flatbed that has the bay), and it is nearer to cargo than `CargoBayDoor` |
| A11 | The transport boat's `transport_rope_winch` is *the* vehicle winch; "`winch` occurs 0 times in the index" | **BROKEN as a census** — a second winch exists in the same parts table: `v1705` medium old fishing boat (`mediumoldfishing_winch`, `crane_winch_*4`, `boom_*_winch_*4`, `cast_net_*3` parented to the winch, 22 rope parts); the motoryacht has 3 `hook_*` and the sailboat a `mast_rope` |
| A12 | No vehicle module type is tether/cargo/rope/winch/tow (53 types) | **HOLDS** |
| A13 | No functional winch class anywhere (0) | **HOLDS** — the 232 graphs' class vocabulary offers only `CVehicleCargoBay` and `CGrapplingHookPropData` |
| A14 | The BmAK `RBatmobileWinch` bound is "at best a force, never a mass", elevator ≈ 2 t class | **HOLDS** — MODLOG §86 says exactly that |
| A15 | Helicopter airlift is UNKNOWN, not "no" | **HOLDS** as a statement (see A7 for the sample limit) |
| A16 | 15.0% / 6.0% / 40.0% of the three carriers | **HOLDS** as arithmetic; inherits A2 and A3 |

**Headline.** Nothing in the donor→tether→mass chain is contradicted by the data: the masses are
real values, the compound entity really contains a tank, the bay really is a 7-member transform
with no capacity, and the tether really has no tune. What needs fixing is (a) the "which vehicle
has a winch" answer, which stops at the transport boat while the fishing boat in the same table
carries a winch plus a crane winch plus a net hung off it, (b) the flatbed sentence, which is
factually wrong, and (c) the mass arithmetic, which quietly treats an UNKNOWN unit as kg and a
6 t target as the car the project is building.

---

## A1 — the masses: 232 entities, donor 975

**Assumption (§1):** `RigidBody.mass` is on 232 entities, 231 with one body, and the donor's value
is 975.

**Test.** Recount from the decoded entity caches.

```
entity caches: 232
entities with a mass: 232 multi-body: 1
entities with 0 masses: []
module types total: 53
```

and the donor plus its two reference vehicles, straight out of the caches:

```
  v0300_car_kensington_sportsmuscle_civilian_01 RigidBody [('mass', 975), ('center_of_mass[0]', 0), … ('use_calculated_inertia', 1), ('add_drivers_mass', 0)]
  v1602_boat_urga_transport_military_01 RigidBody [('mass', 100000), …]
  v4603_plane_urga_cargotransport_military_01 RigidBody [('mass', 40000), …]
```

**Result.** 232/232 have a mass, exactly one entity has two bodies, the donor is 975, the boat
100,000 and the plane 40,000 — every §1 figure. Note that `mass` is one of **17** `RigidBody` rows
(`center_of_mass`, `unit_inertia_*`, `use_calculated_inertia`, `add_drivers_mass`,
`max_linear_velocity`, …) and `use_calculated_inertia = 1` everywhere, so the mass is what the
engine derives inertia from — `mass` is load-bearing, not decorative.

**Verdict: HOLDS.**

---

## A2 — "the unit is UNKNOWN … every comparison is a ratio, never a conversion"

**Assumption (stated §1, twice):** the file gives a number and no unit, so nothing is converted.

**Test 1 — is there any unit in the entity data?** No row names a unit; the only nearby SI-looking
values are positions (`center_of_mass[2] = -23.72` for the 40 t plane, i.e. metres) and the mass
itself. `Buoyancy` carries `buoyancy`, `radius`, `side_area`, `bottom_area` — per-module geometry,
no density to divide by.

**Test 2 — are the numbers kg-plausible across families?** Take the extremes of the same field:

```
v0005_car_autostraad_minetruck_commercial_01      550000     (a mine hauler: real ones are 300–600 t)
v1202_boat_capstone_corvette_rebel_01             150000
v1602_boat_urga_transport_military_01             100000
v4603_plane_urga_cargotransport_military_01        40000     (C-130 empty ≈ 34 t)
v0602_car_urga_armoredtransport_military_01         6000     (the "6 t class" car)
v0300_car_kensington_sportsmuscle_civilian_01        975
bike family, min/max                                60 / 750
```

**Result.** The field behaves like kilogrammes in every family (a 550 t mine truck, a 150 t
corvette, a 40 t transport, a 6 t armoured car, a 975 kg sports car, 60–750 kg bikes). That is
strong circumstantial evidence and no proof: no file states the unit, so the UNKNOWN label is
right. But §1 then prints "a 6,000 car is **15.0%** of the cargo plane's own body mass" — 6,000 is
a kilogramme design value and 40,000 is a field value, so that percentage **is** a conversion.
The document says one thing and does another in the next paragraph.

**Verdict: WEAK.** Keep the UNKNOWN, but either (a) say "taking the field as kg (plausible: mine
hauler 550,000, plane 40,000, car 975)", or (b) drop the percentages and keep only the ×-ratios
against the donor, which are unit-free.

---

## A3 — the target is "6,000", and that is the car

**Assumption (§1, §7):** "Batmobile (WLD-7 design value, not a decoded number) = **6,000** =
**6.154x** the donor".

**Test.** Look up what 6,000 is in this project.

```
v0602 (the 6 t class car in README/MODLOG): [6000] [6000]        <- the file value of the Urga armored transport
README.md:279  … tyre Ø 1.20, 6,000 kg, score 0.134) and the Capstone medium/bavarium tank …
README.md:284  Context for that ranking: our built Batmobile is **mass 4,000 kg**, wheelbase 5.029, track 2.416,
GRAB_BACKLOG.md:139 | DIM-3 | Mass is heavy-armoured (BmAK has no absolute mass; the 6 t class row stands until a lore source exists)
GRAB_BACKLOG.md:231 | WLD-7 | … behave sensibly with a 6 t car
```

**Result.** 6,000 is the `v0602` field value that the project calls the "6 t class", and it is
**not** the car the project is building — the built Batmobile is 4,000 kg. So every percentage in
§1 describes a vehicle 50 % heavier than the one in the dropzone. With 4,000 the same three
numbers are 10.0 % / 4.0 % / 26.7 %, and the donor multiple is 4.103×.

**Verdict: WEAK.** The card is careful to call 6,000 a "design value, not a decoded number" — but
the *build* has a different mass, and WLD-7's question ("does the tether behave with a 6 t car")
is being answered for a car that is 4 t. Quote both columns.

---

## A4 — the compound entity is plane 40,000 + tank 25,000

**Assumption (§2, "the proof that a vehicle rides in a bay"):** `v4603 … military_cargo_tank` holds
two roots (`CAirPlane` + `CCar`) and two bodies, `25,000` (plane) and `40,000` (…), and the mod log
even corrects an earlier reading: "an earlier reading of 'mass = 25,000' was half the picture".

**Test.** Read the compound graph and both standalone entities.

```
  roots: {'CAirPlane': 1, 'CCar': 1}
    CAirPlane v4603_plane_urga_cargotransport_military_01
    CCar      v0201_car_capstone_mediumtank_military_01
   RigidBody rows: [('mass', 40000), …]
   RigidBody rows: [('mass', 25000), …]

standalone plane  mass: [(None, [40000])]
standalone tank   mass: [(None, [25000])]
compound          mass: [(None, [40000]), (None, [25000])]
```

**Result.** The assignment is confirmed twice over: the plane root is named after the plane whose
own file is 40,000, the car root is named `v0201_car_capstone_mediumtank_military_01` whose own
file is 25,000, and the compound lists 40,000 then 25,000 in that order. The first body's
`center_of_mass[2] = -23.72` m also fits a 30 m aircraft rather than a tank.

**Verdict: HOLDS.**

---

## A5 — the bay: 12 on 12, 7 members, no capacity

**Assumption (§2):** `CVehicleCargoBay` appears 12 times, one per entity, with exactly
`_object_id, disable, enable, enabled, name, name_hash, world` and no capacity or mass limit.

**Test.** Union of member names over all twelve, and whether the sets are identical.

```
bays: 12
  union of member names across all 12: ['_object_id', 'disable', 'enable', 'enabled', 'name', 'name_hash', 'world']
  member sets identical: True
   v1602_boat_urga_transport_debug   VehicleCargoBay  {… 'enabled': '1', 'name_hash': '136218203',
       'world': '1,0,0,0, 0,1,0,0, 0,0,1,0, 0,1.292236,-2.511719,1'}
```

**Result.** The union is exactly the seven names quoted, the sets are identical on all twelve, the
only numeric payload is the world transform, and `enable`/`disable` are empty strings on every one.
"There is no capacity field" is a statement about a complete member set, not about a search.

**Verdict: HOLDS.**

---

## A6 — "the boat and the flatbed carry the bay and its door effects"

**Assumption (§2):** "Only the planes have bay interaction points; the boat and the flatbed carry
the bay and its door effects without one."

**Test.** Per-entity object census of everything named `*cargobay*` / `*bay.cargo*`.

```
  v1602_boat_urga_transport_military_01  {4 × SAttachedEffect Door…CargoBay, CVehicleCargoBay}
  v4603_plane_urga_cargotransport_military_01  {2 × point.bay.cargo.*, 2 × entry.reel.to.stunt.bay.cargo.*,
        CPartProp cargotransport_cargobay, 4 × door effect, 12 × Speaker_inside_cargobay*,
        SoundLayer_CargoBay, CVehicleCargoBay}
  v5602_train_urga_monorailflatbed_military_containers   {'CVehicleCargoBay · VehicleCargoBay': 1}
  v5602_train_urga_monorailflatbed_military_empty        {'CVehicleCargoBay · VehicleCargoBay': 1}
```

**Result.** The boat: bay + four door effects, no points — as written. The flatbed: **bay only** —
no door effects, no points, no part prop, no speaker. The sentence groups the two vehicles and
gives the flatbed a door system it does not have. (The counts in the table above it are right:
door effects 10 = 4 boats + 6 planes, points 6 = planes only.)

**Verdict: BROKEN** (small, but it is the difference between "a door opens for you" and "a
transform sits in a flatbed").

---

## A7 — "no helicopter has a bay (0 of 23)"

**Assumption (§2, and the card's Done line):** no helicopter in the fleet has a bay, so a
helicopter airlift has no file carrier.

**Test 1 — how many helicopters are there?** Distinct helicopter leaves in the index:

```
helicopter .ee paths: 41 distinct leaves: 39
  v2102…, v2200…, v2201…, v2601…, v2602… (incl. _custom_mm230), v2603…, v2604… (incl. signature_shielded,
  _di_ravello), w615_helicopter_heavy_missile, w621/w622 …, crashing_helicopter, prototype_boss_helicopter, …
caches that are helicopters: 23
leaves without a decoded cache: 16
  ['crashing_helicopter', 'v2200_helicopter_capstone_assault_blackhand_01',
   'v2601_helicopter_urga_heavyassault_rebel_02', 'v2602_helicopter_urga_lightassault_blackhand_01',
   'v2602_helicopter_urga_lightassault_military_01_custom_mm230', …]
```

**Test 2 — can the undecoded ones be searched?** Read one DLC helicopter `.ee` through the same
reader the census uses:

```
control v2602_helicopter_urga_lightassault_blackhand_01 [dlc] 6206960 B, 1080 printable runs >=8
  sample: ['AVALANCHEARCHIVEFORMATISCOOL', '.ez 5=1w', '-&p$b^HH', 'C:vpdy^^', …]
  contains 'CHelicopter': False   'CVehicleCargoBay': False
```

**Result.** The `.ee` returns as the still-compressed ADF blob (`AVALANCHEARCHIVEFORMATISCOOL` is
the archive header), so a class-name search on it proves nothing either way — the decoder for these
(`jc3grab.grab_ee` → `convertadf`) writes temporary files, so it is out of bounds for a read-only
review. The claim "0 of 23" is therefore true of the **23 decoded** helicopters and silent about
**16** more helicopter entities, four of them DLC variants and one a mission custom (`mm230`) —
exactly the ids where a new carry behaviour would be added. Also, the 24th vehicle in the parts
table and the 1 missing cache are the same entity: `v2602…custom_mm230`.

**Verdict: WEAK.** Write "0 of the 23 decoded helicopters; 16 heli entities (DLC/mission variants)
are not in the decoded set", and let WLD-7 know the census has that hole.

---

## A8 — no tether/grapple tune exists

**Assumption (§1, §5):** all 335 `tether` names in the index are dialogue/icons/videos/decals plus
the two `dualtether_test_to_vehicle` graph files; no tune, so strength is UNKNOWN.

**Test 1 — the path census.**

```
   tether      335
   winch         0
   grapple     620      (all dialogue .ban/.wavc, 11 hmddsc, 1 .ee, 1 .bl, 1 .blo, 2 .stringlookup)
   rope         83      (mesh textures/LODs, propeller false positives)
```

and the seven non-dialogue `tether` paths are the ones the doc lists (one decal, two graphs, two
icons, two videos). No `.wtunec`/`.defc`/`.bin` path contains `tether`.

**Test 2 — content, not names.** Scan every tune/definition/module file under 3 MB for the words:

```
tune/def/module files under 3 MB: 751 totalling 36 MB
files containing tether/grapple/rope_winch/winch: 10
   locations/world.bin                                    grapple
   v1602_boat_urga_transport/transport_vehicle_parts.vmodc  rope_winch
   v1602_boat_urga_transport/transport.physicsc             rope_winch
   v1705_boat_na_mediumoldfishing/mediumoldfishing_vehicle_parts.vmodc  winch
   settings/spawn_combatant_defs.bin                      grapple
```

**Result.** Nothing here is a tether/grapple *tune*: the hits are two part modules, one physics
file, a world list and a combatant tag. The `dualtether` graph itself is a compiled GraphScript ADF
(type names `GSGraph`, `GSNode`, `GSData`; the `.gdc` holds `FIRE_GRAPPLE`) with no constants —
so "strength is UNKNOWN, only a Q-1 probe can measure it" survives the strongest search I can run
without a decoder.

**Verdict: HOLDS.**

---

## A9 — the prop-side tether objects carry no force

**Assumption (§3):** the 33 `CGrapplingHookPropData` objects are markers on loose cargo, with
`enable_event`/`disable_event` empty and no force/distance/mass member.

**Test.** Union of member names over all 33, plus the six `tether_*` objects.

```
hooks: 33
  union of member names: ['_object_id', 'disable_event', 'enable_event', 'enabled', 'name', 'name_hash']
   v0505_car_solar_oldtruck_commercial_cargo_barrel  GrapplingHookPropData  {'enabled': '1', 'enable_event': '', 'disable_event': '', …}

   v0505_car_solar_oldtruck_commercial_cargo_random  tether_yank  keys=['_object_id','disable_event','enable_event','enabled','name','name_hash']
   v0505_car_solar_oldtruck_commercial_cargo_random  tether_tear  keys=[ … same six … ]
   v5602_train_urga_monorailflatbed_military_containers_rigidobject  tether_tear7  keys=[ … same six … ]
```

**Result.** Six keys, no numeric payload, both events empty — so the objects can mark *which prop
may be torn* but cannot carry a threshold. The document's reading is correct.

**Verdict: HOLDS.**

---

## A10 — "67 behaviours, none winch/rope/tow/reel; nearest `CargoBayDoor`"

**Assumption (§4):** of 67 named part behaviours, none is a winch/rope/tow/reel, and the nearest is
`CargoBayDoor` (28 parts).

**Test.** Flatten the parts table (`n` name, `b` behaviour) and count.

```
part rows: 11643
distinct behaviours: 68            (incl. None)
CargoBayDoor rows: 28 ; distinct non-None behaviours: 67
any behaviour with cargo/tether/rope/winch/tow/reel: ['TrainCargo', 'CargoBayDoor', 'Propeller']
```

and the `TrainCargo` rows:

```
  monorailflatbed_container_f   beh=TrainCargo  dt=Train_Generic  parent=0  v5602_train_urga_monorailflatbed…
  monorailflatbed_container_r   beh=TrainCargo  …
  monorailflatbed_pipe_01 … _13 beh=TrainCargo  …   (15 rows in total)
```

**Result.** The count is right (67 non-`None`), and no behaviour pulls, reels or tows — the WPN-6
verdict stands. But there **is** a cargo behaviour: `TrainCargo`, on 15 parts of the very flatbed
that carries the `CVehicleCargoBay`. Calling `CargoBayDoor` "the nearest" skips the one behaviour
whose name and placement say "this part is the cargo". It matters because the card asks how a
vehicle is *held*; `TrainCargo` is the only part-side hint of an attachment, and the doc does not
mention it.

**Verdict: WEAK** — add `TrainCargo` (15 rows, `v5602`), keep "no pull/tow/reel".

---

## A11 — "the transport boat's winch is the carrier; `winch` occurs 0 times"

**Assumption (§4, §5, the WPN-6 answer):** the winch geometry is `transport_rope_winch` on the
transport boat (one part, 6 LOD files, 12 fleet-wide); `winch` matches 0 index paths, supporting
"no winch mechanic".

**Test 1 — the parts table is already in the tool's inputs. Search it for winches.**

```
== every part name (fleet-wide) containing winch/crane/rope/reel/hook/tow ==
  v1705_boat_na_mediumoldfishing_civilian_01:
     mediumoldfishing_winch            i=39  beh=None  dt=Boat_Generic  parent=0
     mediumoldfishing_crane_winch_l_l  i=65  beh=None  dt=Boat_Antenna  parent=2
     mediumoldfishing_crane_winch_l_r  i=66  …
     mediumoldfishing_crane_winch_r_l  i=67  …
     mediumoldfishing_crane_winch_r_r  i=68  …
     mediumoldfishing_boom_l_winch_d   i=99  …  parent=63
     mediumoldfishing_boom_l_winch_t   i=100 …
     mediumoldfishing_boom_r_winch_d   i=101 …  parent=64
     mediumoldfishing_boom_r_winch_t   i=102 …
     mediumoldfishing_crane_c          i=2   …
     mediumoldfishing_cast_net_c       i=95  …  parent=39   <- parented to the winch
     mediumoldfishing_cast_net_l/r     i=96/97 … parent=39
     mediumoldfishing_rope_buoy_* x18, mediumoldfishing_rope_tire_* x4, mediumoldfishing_ropes
  v1300_boat_kensington_motoryacht:  motoryacht_hook_01..03
  v1302_boat_kensington_sailboat:    sailboat_mast_rope
```

**Test 2 — the vehicle's own file list confirms it is modelled, not just named.**

```
  v1705_boat_na_mediumoldfishing_civilian_01   (parts module + deform + physicsc all contain 'winch'):
     mediumoldfishing_vehicle_parts.vmodc, mediumoldfishing_vehicle_deform.vmodc, mediumoldfishing.physicsc
```

**Result.** There are **two** vehicles with winch parts, and the second one is a better carrier
story than the first: the fishing boat's winch (`i=39`) is the parent of the cast-net parts
(`i=95..97`), i.e. a rope-like part hangs off the winch, and the crane has its own four winch parts
with a boom. The doc's claim "`winch` occurs 0 times in the index" is true of *paths* and
irrelevant — the word occurs 10 times in the parts table the same script reads, plus deform and
physics modules. So "a carrier exists for the geometry" is right, but it is understated and
described as if only one vehicle had one.

**Verdict: BROKEN as a census** (the conclusion "no winch *mechanic*" is still right: all of them
are `behavior = None` meshes).

---

## A12 — no vehicle module type is tether/cargo/rope/winch/tow

**Test.** All 53 module types from the 232 caches, matched against the vocabulary.

```
modules types total: 53
module types matching cargo/magnet/tow/lift/rope/winch/grapple/crane/hook: {'Propellers': 38}
```

**Result.** The only hit is the known substring trap (`Pro`**`rope`**`llers`), which the script
already documents. `Propellers` carries rotors, not rope.

**Verdict: HOLDS.**

---

## A13 — "functional winch classes anywhere in the fleet: 0"

**Test.** Class census over all 232 `.epe` graphs, vocabulary `cargo|magnet|tow|lift|rope|winch|grapple|crane|hook`.

```
   SAttachedEffect                      5342 objects on 232 entities
   SDynamicAttachedEffect               4344 objects on 228 entities
   CInteractionGraphIsAttachedCondition  171 objects on 170 entities
   CGrapplingHookPropData                 33 objects on   3 entities
   CVehicleCargoBay                       12 objects on  12 entities
```

**Result.** The only two "carrier" classes in the whole entity set are the two the document names;
everything else is an effect or an attached-condition. There is no `CMagnet`, no tow hook, no
winch class.

**Verdict: HOLDS** (strengthened: this is a complete class census, not a name search).

---

## A14 — the quoted BmAK bound

**Assumption (§4 last paragraph, §7):** "MODLOG §86/§87: `RBatmobileWinch` yields at best a force,
never a mass … §86 shows that bound is an elevator bound (>= ~2 t class)".

**Test.** Read §86 verbatim.

```
## 86. Winch feats cannot derive mass: every path is underdetermined (2026-10-16)
- **Elevator lift** bounds the WINCH (force >= elevator + 2 occupants ≈ 2 t class), not the vehicle.
  The Batmobile's mass does not appear in that inequality at all — wrong direction.
- **Bearing the vehicle's weight** is static equilibrium T = m·g with T (cable tension/rating)
  unknown: one equation, two unknowns, circular.
- File-side check: `RBatmobileWinch` / `Default__RBatmobileWinch` exist only as name-table IMPORTS …
```

**Result.** The quotation is faithful, including the "wrong direction" caveat that most reports of
this kind drop. §87 adds that the class default lives in a compressed `BmGame.upk`, unreachable.

**Verdict: HOLDS.**

---

## A15 — helicopter airlift is UNKNOWN

**Test.** Object census of the 23 decoded helicopter graphs against
`carry|airlift|tow|sling|hook|winch|cargo|magnet|lift`:

```
helicopter graphs: 23
  heli objects matching carry/airlift/tow/sling/hook/winch/cargo/magnet/lift: (none)
```

**Result.** No object of any class in a decoded helicopter has a carry-ish name, on top of the zero
bays. Since the mechanism would be native (the bay's attach rule already is), UNKNOWN is the right
label rather than "no".

**Verdict: HOLDS** — with A7's sample caveat attached.

---

## A16 — the three percentages

**Test.** Arithmetic, and the underlying carrier values.

```
  6,000 / 40,000 = 15.0 %     6,000 / 100,000 = 6.0 %     6,000 / 15,000 = 40.0 %
  family train: n=12 min 15,000 median 22,000 max 40,000
  donor: 6,000 / 975 = 6.154x
```

**Result.** The arithmetic is right for all four numbers, and the flatbed's 15,000 is the family
minimum. The values are what they say — but see A2 (unit) and A3 (which car).

**Verdict: HOLDS** as arithmetic.

---

## What this changes

* **Keep:** the mass table and the donor's 975 (A1); the compound plane+tank proof, now confirmed
  against the two standalone entities (A4); the bay's seven members and missing capacity (A5); the
  "no tether tune" answer, now backed by a content scan (A8); the prop-marker reading (A9); the
  module-type and class censuses (A12, A13); the BmAK quotation (A14); the corrected compound-mass
  reading.
* **Fix the flatbed sentence (A6):** it has the bay and nothing else — no door effects, no points.
  The boats have door effects; the planes have points, entries, the part prop and the speaker set.
* **Fix the winch census (A11):** the transport boat is not the only vehicle with winch geometry.
  The `v1705` fishing boat carries a winch with a cast net hung off it, a four-part crane winch and
  a boom pair; the motoryacht has three hooks and the sailboat a mast rope. WPN-6 should say: "two
  vehicles model a winch (`v1602` transport, `v1705` fishing boat); every one is a `behavior = None`
  mesh, so the geometry is copyable and the mechanism is still absent."
* **Add `TrainCargo` to the behaviour list (A10)** — 15 rows on the flatbed that owns the bay; it is
  the nearest thing to a cargo attachment in the parts data, nearer than `CargoBayDoor`.
* **Label the mass unit (A2)** and **give the percentages for 4,000 as well as 6,000 (A3)** — the
  built car is 4,000 kg, and the unit is inferred, not stated.
* **Bound the helicopter claim (A7):** 0 of 23 *decoded*; 16 heli entities are undecoded, four of
  them DLC. Either decode them (the ADF converter writes temporaries) or say so in the UNKNOWN list.
