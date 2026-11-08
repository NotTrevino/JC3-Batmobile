# Assumption challenge — G2-31 · water behaviour

**Card:** `GRAB_BACKLOG.md` §G2-31 (line 793), §12 row (line 1314), decision D-8 (line 1264).
**Outputs challenged:** `Research/JC3Grab/WATER.md`, `WATER.json`, `Tools/scripts/jc3water.py`,
MODLOG §"G2-31 · Water behaviour — done" (line 10816).
**Rules applied:** §0.5 (R1–R14), especially R5 (a member is what it does, not what it is called),
R4, R11.

**Method.** Everything below was re-derived from what is on disk: the 232 entity caches in
`E:/Modding/JustCause3/_grab/entities/`, the 232 object graphs in `E:/Modding/JustCause3/_grab/detail/`,
`Builds/test-091/…civilian_01.ee` (decoded with `jc3detail` + `jc3adf`), the decoded script tree
`E:/Modding/JustCause3/_grab/hud/dec/scripts/`, and `Research/JC3Grab/INDEX.jsonl`. No game was launched,
nothing was written under `D:/Games`, nothing committed, no archive edited. This report is the only
file written.

---

## VERDICT summary

| # | assumption | verdict |
|---|---|---|
| 1 | `will_sink` 1 = "sinks and stalls", 0 = "floats" | **WEAK** — a clean, perfectly separating bit, but the behaviour is the name; no engine or in-game evidence on disk |
| 2 | the other 43 split "cleanly by module" (35 boat + 8 floating) | **HOLDS** — 35 `BoatBuoyancy` entities, all `will_sink` 0, no second instance anywhere |
| 3 | "`will_sink` is the only scalar that separates the sinking cars from the amphibious eight" | **BROKEN** — the 8 also carry `angular_drag_roll` 0.1/0.2, `…_at_speed` 0.85, `…_ref_speed_kmph` 150, `drag_falloff_power` 0.4, `anti_penetration_max_accel` 30 |
| 4 | "these eight float because `will_sink` is 0, not because their lift differs" | **BROKEN** — the sea scout's lift curve differs (`buoyancy_factor_vs_speed_ms.x_max` 1 vs 20) |
| 5 | the unit behind `_ms` is UNKNOWN ("10/20 ms is too short to be a drown timer") | **BROKEN** — the same shared module decodes `_ms` as **m/s** in seven sibling members; 10/20 are water-**entry speeds**, not timers |
| 6 | `engine_shut_down_delay_s` 30 (car) / 5 (others) = "the engine stalls after 30 s" | **WEAK** — values hold; `_s` = seconds is consistent, the *stall* is the name |
| 7 | "no vehicle overrides any of them" (one shared `vehicle_common.vmodc`) | **HOLDS** — one file path for 232 entities, every row single-valued ×232 |
| 8 | "no `drown`/`submerge`/`flood`/`swim`/`underwater` path anywhere" | **HOLDS** for the 52 vehicle module types and the object graphs; **WEAK** on "anywhere" — the script layer ships a drowning HUD |
| 9 | "38 distinct water-ish member paths" | **HOLDS** the number; the §9 table sums to 40 (two paths live in two modules) |
| 10 | "the build's water modules are identical to the donor" | **WEAK** — true, but the check compares 8 members of 86 comparable ones and none of the hull arrays |
| 11 | "the hull is a `part_elements[]` triangle mesh built from `sportsmuscle_body`" | **HOLDS** the reference; **WEAK** the mesh/shape reading (88 verts / 128 triangles, a ±2.6 m envelope against a 2.10 × 1.39 × 3.72 m body) |
| 12 | "R3: nothing to change — the hull is a collider, not a physics station" | **WEAK** — the collider is the donor's baked data and nothing compares it with the body the build actually ships |
| 13 | "10 of 189 ship an empty hull and still sink, so the mesh is not the switch" | **WEAK** — circular: "still sink" means `will_sink` 1 |
| 14 | one entity carries a water module twice (cargo plane) | **HOLDS** — 2 `Buoyancy` + 2 `WaterInteraction`, one of each the medium tank's |
| 15 | the counts: 232 / 189 / 8 / 35 / 21 rows / 604 files / 52 module types | **HOLDS** — every one reproduced |
| 16 | `--check` proves the document | **WEAK** — it proves the document equals its generator; §3's false sentence and §7's unit claim are generated prose and pass |
| 17 | D-8 / WLD-6: "sinks and stalls by default, no water edit needed" | **WEAK** — see 1, 5, 6: the bit is real, the *stall* and the *kill* carriers are a 30 s timer and a 10/20 **m/s** entry threshold |

Headline: **the census is exact and the classification is reproducible; two of the card's
explanations are contradicted by its own tables (§3, §4), and §7/§10 mis-read the `_ms` members.**
The fleet's own shared module decodes `_ms` as metres per second, so `min_water_entry_ms` 10 /
`fatal_water_entry_ms` 20 are entry-*speed* thresholds (36 / 72 km/h), not drown timers. What a
submerged car then does is still unknown — but for a different reason than the card gives, and the
"kill side" it names is not on the sinking path at all.

---

## 1. `will_sink` 1 = "sinks", 0 = "floats"

**Claim.** §1: "`WaterInteraction.will_sink = 1` … sinks and stalls (189)"; the whole classification
is `group()` in `jc3water.py`: `BoatBuoyancy` → boat, else `will_sink == 1` → sink, else floating.

**Test.** Is the bit clean, and is there anything but the name behind it?

```
$ python Tools/scripts/jc3water.py --check
PASS: 232 entities, sink 189 / floating 8 / boat 35 …
groups {'sink': 189, 'floating': 8, 'boat': 35} entities 232
entities with BoatBuoyancy: 35 with will_sink!=0: [] with 2 BoatBuoyancy: []
empty part_elements: 10   will_sink of those: [1]
(group,hulls): [(('boat', 1), 35), (('floating', 1), 8), (('sink', 0), 10), (('sink', 1), 179)]
```

The split is perfect — 43 zeros, 189 ones, no entity disagreeing with its module set, `will_sink`
never outside {0,1}. But no file states what the bit *does*: there is no engine trace, no script
consumer, no in-game observation on disk. The card's own §10 answers "does the build sink like a car
today? **yes**" from this bit.

**Result.** The bit is a decoded value; "sinks" is the field name. That is exactly the R5 case the
§0.5 rules warn about. It is *plausible* (a module called `WaterInteraction` carrying `will_sink`
next to hull and drag data), and the clean 43/189 split is consistent, but nothing on disk
distinguishes "will sink" from "participates in water" or "cannot float".

**Verdict: WEAK** (name-based behaviour, honestly hedged nowhere).

## 2. The 43 split by module: 35 boats + 8 floaters

**Claim.** §1/§5: 35 boats carry `BoatBuoyancy`; 8 land/air vehicles (`v0200` APC ×3, `v2603` sea
scout ×3, `v4500` floatplane ×2) keep a plain `Buoyancy` and do not sink.

**Test.** Counted directly, and checked the failure mode the classification could hide — an entity
with `BoatBuoyancy` *and* `will_sink` 1 would be labelled "boat" without floating:

```
entities with BoatBuoyancy: 35   with will_sink!=0: []   with 2 BoatBuoyancy: []
WATER.json duplicates: v4603…cargo_tank: Buoyancy ×2, WaterInteraction ×2
census: {"entities": 232, "groups": {"boat": 35, "floating": 8, "sink": 189},
         "part_elements": {"boat": {"1": 35}, "floating": {"1": 8}, "sink": {"0": 10, "1": 179}}}
```

**Result.** Holds exactly. No boat carries `will_sink` 1, no floaters overlap, the 8 are the three
APC builds, the three sea-scout builds and the two floatplane builds, and every one of the 43 has
exactly one hull element.

**Verdict: HOLDS.**

## 3. "`will_sink` is the only scalar that separates the sinking cars from the amphibious eight"

**Claim.** §3: "`will_sink` is the only scalar that separates the sinking cars from the amphibious
eight: both groups carry the same `angular_drag_*` 0.05, `pressure_drag` 5000 / `pressure_drag_2`
20000, `suction_drag` 5000, `depth_full_drag` 0.1 and `reference_drag_speed_ms` 20."

**Test.** Print the eight floaters' `WaterInteraction` scalars and the 189 sinkers' distribution.

```
floaters (all 8), selected scalars:
  v0200 APC ×3                 roll 0.1  roll@spd 0.85  ref_kmph 150  falloff 0.4  buoy_x_max 20  anti_acc 30
  v2603 sea scout ×3           roll 0.2  roll@spd 0.85  ref_kmph 150  falloff 0.4  buoy_x_max  1  anti_acc 30
  v4500 floatplane ×2          roll 0.1  roll@spd 0.85  ref_kmph 150  falloff 1.0  buoy_x_max 20  anti_acc 15

sinkers (189), same columns:
  170 × (0.05, 0.05, 50, 1, 20, 15)
   19 × (0.05, 0.75, 150, 0.4, 20, 30)
```

No floater has `angular_drag_roll` 0.05; none has `angular_drag_roll_at_speed` 0.05; all eight have
`angular_drag_ref_speed_kmph` 150. Three scalars take values that no sinking entity ever shows:

```
WaterInteraction scalars whose floater value never occurs on a sinker: 3
    angular_drag_roll          floaters [0.1, 0.2]   sinkers [0.05]
    angular_drag_roll_at_speed floaters [0.85]       sinkers [0.05, 0.75]
    will_sink                  floaters [0]          sinkers [1]
```

The document contradicts itself here: its own §2 member table lists
`angular_drag_roll 0.05 .. 0.2 (4 distinct)` and `angular_drag_roll_at_speed 0.05 .. 0.85 (4
distinct)` — the upper ends are the floaters.

**Result.** The sentence is false as written, and the difference is not cosmetic: roll damping and
the reference speed are the terms that decide how a hull behaves at the water surface, which is
exactly the behaviour being classified.

**Verdict: BROKEN.**

## 4. "These eight float because `will_sink` is 0, not because their lift differs"

**Claim.** §5 (and the §1 table row "floats (amphibious)"): "the lift comes from the same `buoyancy`
scalar the sinking cars carry"; "these eight float because `will_sink` is 0, not because their lift
differs".

**Test.** Compare the lift/anti-penetration terms, not just the drags:

```
v2603 sea scout vs a sinking helicopter (v2200 assault), WaterInteraction scalars that differ: 9
    angular_drag_ref_speed_kmph     150   vs 50
    angular_drag_roll               0.2   vs 0.05
    angular_drag_roll_at_speed      0.85  vs 0.05
    anti_penetration_max_accel      30    vs 15
    anti_penetration_multiplier     1     vs 2
    buoyancy_factor_vs_speed_ms.x_max 1   vs 20
    drag_falloff_power              0.4   vs 1
    planing_vs_forward_speed_ms.number_of_control_points 2 vs 5
    will_sink                       0     vs 1
```

`buoyancy_factor_vs_speed_ms` is the lift curve: on the sea scout it is flat up to **1** m/s, on the
sinking helicopter up to **20** m/s. The scalar `buoyancy` is 0.25 on the sea scout and (per the
card) "the same `buoyancy` scalar the sinking cars carry" — the seascout's 0.25 is *lower* than the
donor's 2, so the scalar alone would make it sink harder, not float.

**Result.** The eight floaters are a separately tuned water class: different roll damping, different
reference speed, different anti-penetration, different lift curve. Whether `will_sink` 0 *causes* the
floating or merely accompanies it is exactly what the data cannot say; the sentence claims the former
and the tuning says the latter is at least as likely.

**Verdict: BROKEN** (the "nothing else differs" premise is false; the causal claim is unsupported).

## 5. The `_ms` unit: "UNKNOWN — 10/20 ms is too short to be a drown timer"

**Claim.** §7: "the unit behind the `_ms` suffix is not decoded here (`UNKNOWN`): 10/20 ms is too
short to be a drown timer, so the name is the only evidence of what the numbers mean"; §10: "the only
death-on-water member in the fleet is `vehicle_damage.fatal_water_entry_ms` = 20 … do not quote it
as seconds or as damage".

**Test.** Every `_ms` member in the fleet's vehicle modules, with its value — the same shared
`vehicle_common.vmodc`, same author, same suffix:

```
tire_effects.min_skid_velocity_for_skid_ms        0.5     (VehicleCommon)
tire_effects.min_slip_velocity_for_spin_ms        1       (VehicleCommon)
vehicle_damage.fire_spreading_speed_ms            1.5     (VehicleCommon)
car_common.crash_min_vel_change_ms                20      (VehicleCommon)
car_common.crash_in_air_min_vel_change_ms         5       (VehicleCommon)
boat_common.crash_min_vel_change_ms               20
motorbike_common.crash_min_vel_change_ms          15
helicopter/plane_common.crash_min_vel_change_ms   20
docking_controls.max_docking_speed_ms             20      (Propellers)
docking_controls.optimal_docking_speed_ms         10      (Propellers)
reference_drag_speed_ms                           20      (WaterInteraction)
reference_speed_ms                                20/30   (Fins)
vehicle_damage.min_water_entry_ms                 10      <- the card's "timer"
vehicle_damage.fatal_water_entry_ms               20      <- the card's "timer"
vehicle_damage.min_water_entry_floating_ms        20
vehicle_damage.fatal_water_entry_floating_ms      50
```

Every sibling decodes `_ms` as **metres per second**, because the name says what it is a speed *of*
(`…_velocity_…`, `…_speed_…`, `…_vel_change_…`) and the value is a speed (0.5 m/s to skid,
1 m/s to spin a wheel, 1.5 m/s fire spread, 20 m/s reference drag). The same module mixes the two
conventions explicitly: `angular_drag_ref_speed_kmph` (km/h) sits next to `reference_drag_speed_ms`
(m/s), and `planing_vs_forward_speed_ms.x_max` 20 is a speed axis. There is no `_ms` member anywhere
in the fleet whose value only makes sense as milliseconds.

**Result.** `min_water_entry_ms` 10 and `fatal_water_entry_ms` 20 are **entry-speed thresholds**:
entering water at 10 m/s starts something, at 20 m/s it is fatal; floating hulls tolerate 20 and 50.
That reads like the `crash_min_vel_change_ms` 20 family — an impact threshold — and it is *not* a
drown timer at any reading. Consequences:

1. §7's "the *kill* side is fleet-wide: `min_water_entry` 10 and `fatal_water_entry` 20" puts a
   water-*impact* pair on the sinking path. A car that slides gently under the surface never crosses
   10 m/s and therefore never trips either member.
2. §10's answer "can it drown its own engine at depth? the only death-on-water member … is
   `fatal_water_entry_ms` = 20" answers a different question (a hard splashdown) and leaves the
   actual drown-at-depth question with **no** decoded carrier — which is the correct conclusion, but
   reached for the wrong reason and stated as "UNKNOWN unit" rather than "this member is a speed".
3. The card's own §10 warning ("do not quote it as seconds") is right and understated: it can be
   quoted as m/s, from the file.

**Verdict: BROKEN.** This is the one finding that changes the meaning of a value the card prints.

## 6. `engine_shut_down_delay_s` 30 (car) / 5 (others)

**Claim.** §7 and §10: cars lose their engine 30 s after water entry, all other classes after 5 s;
"`car_common.engine_shut_down_delay_s` 30".

**Test.** Values and the suffix convention:

```
boat_common.engine_shut_down_delay_s        5  x232
car_common.engine_shut_down_delay_s        30  x232
helicopter_common.engine_shut_down_delay_s  5  x232
motorbike_common.engine_shut_down_delay_s   5  x232
plane_common.engine_shut_down_delay_s       5  x232
```

Compare the fleet's other `_s` members, which are all durations and all plausible as seconds:
`burn_duration_s` 20, `explosion_delay_s` 5..10, `vulnerable_duration_s` 5.

**Result.** The values hold and `_s` = seconds is the consistent reading (unlike `_ms`, this suffix
is used only for durations). The *stall* is the name: no file says the engine stops, or that the
delay is measured from water entry rather than from submersion depth. It is the best-supported water
member in the card, and still a name-read.

**Verdict: WEAK.**

## 7. "No vehicle overrides any of them"

**Claim.** §7: all 232 entities point at one shared `vehicle_common.vmodc`, so the timers are
fleet-wide and changing them needs a private copy (R7).

**Test.** Distinct module file paths and distinct values per row:

```
distinct VehicleCommon files: 1
  [('editor/entities/jc_vehicles/00_shared/modules/vehicle_common.vmodc', 232)]
constants rows: 21   (every row a single value ×232, e.g. min_water_entry_ms 10 x232)
```

**Result.** Exactly one file, every value single-valued across all 232 modules — no per-vehicle
override exists in the cache, and the "one shared file" claim is right in the strong sense (the
values, not just the path, are identical).

**Verdict: HOLDS.**

## 8. "No `drown` / `submerge` / `flood` / `swim` / `underwater` path anywhere"

**Claim.** §9: "There is no `drown`, `submerge`, `flood`, `swim` or `underwater` path anywhere in the
232 entities"; the module-type scan covers 52 types.

**Test A — the module scan.** Reproduced: 38 distinct paths, all in the six modules the card lists
(`WaterInteraction` 17, `BoatBuoyancy` 9, `HelicopterModel` 5, `VehicleCommon` 5, `Buoyancy` 3,
`Fins` 1); no `drown`/`submerge`/`flood`/`swim`/`underwater` member.

**Test B — outside the modules.** The card's scan only reads module rows. G2-28's finding was that
the entity *root* carries members no module has (`health`, `invulnerable`), so the same place has to
be searched. Every water-ish property name in the 232 object graphs (91,157 objects):

```
distinct water-ish object property names: 2
   buoyancy            513  ['CAirPlane','CBoat','CCar','CHelicopter']
   water_interaction   233  ['CAirPlane','CBoat','CCar','CHelicopter']
```

So no root-level amphibious/drown flag — the negative survives the wider search.

**Test C — the script layer.** `E:/Modding/JustCause3/_grab/hud/dec/scripts/` (260 `.as` files) has a
drowning UI:

```
hud.as:959   private const OXYGEN_DROWNING_THRESHOLD:Number = 28;
hud.as:3687  if(oxygen <= this.OXYGEN_DROWNING_THRESHOLD) … this.ShowDrowning();
hud.as:3707  public function HideDrowning()
hud_fla/drown_4.as   (a HUD symbol, 183 frames)
```

and `INDEX.jsonl` carries water assets (`def_water.effc`, `t_water_splash_*.ddsc`,
`water_traffic.nl`, `water_combat/*.ee`).

**Result.** For **vehicle modules** the claim holds, and holds even against the object graphs. "Any
where" does not: the game ships a drowning mechanic exposed to the HUD script (an oxygen threshold of
28), and water effects/traffic files exist in the index. None of that is a vehicle
"drives-underwater" carrier, so the conclusion survives — the scope sentence does not.

**Verdict: HOLDS for the 52 module types / WEAK as "anywhere".** Note also that the HUD's threshold
`28` is a number with no unit suffix, in the same order of magnitude as 10/20/50 — a reminder that
the `_ms` values in §5 are the only place the project can settle a unit, and it can.

## 9. "38 distinct water-ish member paths"

**Claim.** §9 table: `WaterInteraction` 17, `BoatBuoyancy` 9, `HelicopterModel` 5, `VehicleCommon` 5,
`Buoyancy` 3, `Fins` 1 — "38 distinct member paths".

**Test.** Recompute:

```
scan distinct paths: 38
   WaterInteraction 17 | BoatBuoyancy 9 | HelicopterModel 5 | VehicleCommon 5 | Buoyancy 3 | Fins 1
sum per module: 40
```

The two extra are paths that exist in two modules (`buoyancy_modules` and
`buoyancy_modules[].position[]` are in both `Buoyancy` and `BoatBuoyancy`), so the distinct total is
38 while the column adds to 40.

**Result.** The number is right and reproducible; the table cannot be summed to it, and the document
does not say why. Minor, but it is the kind of thing a reader will try.

**Verdict: HOLDS the number, WEAK the presentation.**

## 10. "The build's water modules are identical to the donor"

**Claim.** §8: "Comparison against the donor cache: **identical**. Every compared member matches";
MODLOG: "build water modules identical to the donor: True"; the check line prints it.

**Test.** What the code compares, and what else is comparable. `build_vs_donor()` checks
`will_sink` + hull-part count + the six `Buoyancy` scalars — **8 values**. Decode the build's module
fresh and diff **all** 734 rows against the donor cache, normalising the path-spelling change between
the cache's writer and today's walker (`control_points[0]x` vs `control_points[0].x`):

```
inner files 604
build WaterInteraction rows 734 | donor cache rows 734
WaterInteraction: common 86, only-build 648, only-cache 648, value diffs 3
   flat_water_vs_speed_ms.control_points[4].x   4.56927081806965e+19  vs 4.56927082e+19
   flat_water_vs_speed_ms.control_points[4].y   4.569208805613843e+19 vs 4.56920881e+19
   flat_water_vs_speed_ms.control_points[4].y2  4.569208365809192e+19 vs 4.56920837e+19
Buoyancy: 10 rows, 10 common, 0 only-build, 0 only-cache, 0 value diffs
```

The three "diffs" are float32 print rounding at 1e19 (the card already notes this class of artefact
in §9's uninitialised tails). The 648+648 "only" rows are the hull arrays: the cache stores
`part_elements[0].hull.vertices` as one flattened row, a fresh decode expands it to 264 floats and
384 index bytes.

**Result.** Everything comparable matches — better than the card claims. But the card's headline
word is "identical", and the one thing that is **not** compared is the hull geometry: 88 vertices
and 128 triangles that decide where the water plane touches the car. The honest statement is
"identical on 86 of 86 comparable members; the hull arrays cannot be compared from the cache".

**Verdict: WEAK** (right answer, overstated coverage).

## 11. "The hull is a `part_elements[]` triangle mesh built from `sportsmuscle_body`"

**Claim.** §1 table and §10: "the hull mesh in `WaterInteraction.part_elements[]` is built from the
donor body part `sportsmuscle_body` and is a water-plane collider".

**Test A — the reference.**

```
build  part_elements[0].from_part.string = sportsmuscle_body   hash 3076414876
cache  part_elements[0].from_part.string = sportsmuscle_body   hash 3076414876
build dump: 'sportsmuscle_body' occurs 130 times  (the part survives in the build)
```

**Test B — the geometry.**

```
vertex rows 264 (float)   -> 88 points
triangle rows 384 (uint8 indices) + 1 array row -> 128 triangles
extents: axis 0 -2.651 .. 2.536 | axis 1 -2.571 .. 2.560 | axis 2 -2.651 .. 2.560
radius from origin: 0.202 .. 2.805, mean 1.728
```

The donor body mesh, from the same project's detail JSON:
`sportsmuscle_body_lod1.rbm  size_m x 2.099  y 1.3875  z 3.7198`.

**Result.** The *reference* holds exactly (same part name and hash in build and cache). The *shape*
reading does not follow: an 88-point hull with ±2.6 m on all three axes is not the donor body's
2.10 × 1.39 × 3.72 m envelope, and no file in the project says how the vertex array is scaled
(`Buoyancy.radius` 0.55, `side_area` 1.85, `bottom_area` 3 sit right next to it and are the obvious
candidates). Calling it "a triangle mesh the game pushes through the water plane" is a name/inference
chain, not a decoded mechanism.

**Verdict: HOLDS the part reference / WEAK the mesh claim.**

## 12. "R3: nothing to change — the hull is a collider, not a physics station"

**Claim.** §10 final row: "anything to change for R3 (physics follows the asset)? no: the hull mesh
… is built from the donor body part `sportsmuscle_body` and is a water-plane collider, not a physics
station".

**Test.** Compare the collider with the body the build actually ships. The water hull is the donor's
baked 88-point data in the donor's own module file; the build's body is the Batmobile model (the
`.ee` still carries the donor's body textures and the part name, and G2-27's rigid parts are separate
entities). Nothing in `jc3water.py` measures the build's body, and nothing compares the two.

**Result.** "Not a physics station" is right (it is not in the `physicsc`), but the R3 conclusion
("nothing to change") needs the collider to match the body, and that is not shown. If the Batmobile
body is longer/taller than the Serpente's, the water contact plane is the donor's silhouette and the
car will float/sink with the wrong waterline. This is cheap to answer (compare the build's body mesh
AABB with the hull's), and the card does not.

**Verdict: WEAK.**

## 13. "10 of 189 ship an empty hull and still sink, so the mesh is not the switch"

**Claim.** §3: "Ten of the sinking entities ship an **empty** `part_elements[]` … They still set
`will_sink` 1, which is why the hull mesh must be read as the shape the water plane pushes against,
not as the sink switch: the switch is the scalar."

**Test.** The data half:

```
empty part_elements: 10   will_sink of those: [1]
   v0009 modernsaloon civilian/debug/premium, v0866 ladbil civilian/debug,
   v3001 snowmobile debug, v3600 combatdirt debug/military/rebel, v9999 dlctestcar debug
```

**Result.** The ten exist and all carry `will_sink` 1. But "**still sink**" is not an observation —
it is the same `will_sink` bit being read back. The argument is: "they sink (because will_sink says
so), therefore the mesh is not what makes them sink". That is circular; the only non-circular version
is "will_sink is set even where there is no hull, so the two are independent members", which is much
weaker and does not need the word "sink".

**Verdict: WEAK** (correct data, circular inference).

## 14. "One entity carries a water module twice"

**Claim.** §2 table: `v4603_plane_urga_cargotransport_military_cargo_tank.ee` has 2 `Buoyancy` and 2
`WaterInteraction`, one of each the medium tank's; "both copies say `will_sink` 1".

**Test.** `WATER.json` `duplicates`:

```
Buoyancy ×2:  v0201_car_capstone_mediumtank_buoyancy.vmodc
              v4603_plane_urga_cargotransport_buoyancy.vmodc
WaterInteraction ×2: v4603_plane_urga_cargotransport_water_interaction.vmodc
                     v0201_car_capstone_mediumtank_water_interaction.vmodc
```

and both `will_sink` values are 1 (the entity sits in `sink`, hulls 1).

**Result.** Exact, including the tank's module being the second one. This is also the entity that
carries two `VehicleDamage` modules in G2-28 — the same cargo-tank variant, so the "233 modules in
232 entities" arithmetic has one known cause.

**Verdict: HOLDS.**

## 15. The counts

**Claim.** `--check` line: 232 entities, sink 189 / floating 8 / boat 35, donor `will_sink` 1
`buoyancy` 2 `drag` 100 (1 hull element), 35 boats `base_buoyancy` 0.1..1.45, 21 fleet-wide rows,
build identical, 38 paths; §8: 604 inner files; §9: 52 module types; §2: `Buoyancy` 198,
`WaterInteraction` 233 instances, `BoatBuoyancy` 35.

**Test.** All reproduced in this session:

```
entities 232 | groups {'sink': 189, 'floating': 8, 'boat': 35}
module types (incl None): 53 named: 52
Buoyancy n=198  WaterInteraction n=233  BoatBuoyancy n=35      (member census)
constants rows 21 | scan paths 38 | build container_files 604
donor: will_sink 1, buoyancy 2, drag 100, radius 0.55, side_area 1.85, bottom_area 3,
       up_velocity_cap 20, 1 hull element (from_part sportsmuscle_body)
boats: base_buoyancy 0.1 (v1701) / 1 / 1.45 (v1202, v1302, v1705, v1717), pontoons 6 or 9
```

**Verdict: HOLDS** — every number.

## 16. What `--check` proves

**Claim.** §11: "Every number here is regenerated by the script from the decoded cache and the
build's own `.ee`; none is typed by hand." MODLOG's tamper test shows the md/json comparison failing
on an edited number.

**Test.** `python Tools/scripts/jc3water.py --check` → exit 0, the PASS line above. The check
re-renders the markdown from the payload and compares bytes.

**Result.** It proves the document equals its generator, which is what catches a hand-edited table
cell. It cannot catch a wrong sentence that the generator writes, and two of the card's claims are
exactly that: §3's "only scalar" paragraph and §7's `_ms` unit paragraph are generated prose, so
`--check` passes while both are false. A reader who takes the PASS line as "the analysis is verified"
is misled.

**Verdict: WEAK** (necessary, not sufficient).

## 17. D-8 / WLD-6: "the build sinks and stalls by default, no water edit needed"

**Claim.** §10 table: does the build sink like a car today? **yes**; does it need any water edit for
the lore route? **no**; could it float instead? only with `will_sink` 0 plus a `BoatBuoyancy` block.

**Test.** The three legs the sentence stands on:

1. `will_sink` 1 on the build's own module — verified (`will_sink` 1, identical to the donor).
2. "stalls": `car_common.engine_shut_down_delay_s` 30 — a value, with `_s` a consistent seconds
   suffix, but no carrier that says the engine stops (§6).
3. "sinks" / drown: the card's kill side is `min/fatal_water_entry_ms` 10/20 — which §5 shows are
   **m/s entry speeds**, not timers.

**Result.** The first leg is solid. The second is a name-read with a plausible unit. The third leg is
misidentified: the fleet has no decoded drown-at-depth carrier (the card's own §9 says so), and the
members it does name are splashdown thresholds. So "sinks and stalls by default" is:
- *supported* for "participates in water as a non-amphibious vehicle" (the bit + the shared file),
- *unproven* for "the engine stalls" and
- *wrongly supported* for "it dies in water" (a hard splash kills it, a gentle sink does not).

The float route's cost ("`will_sink` 0 plus a `BoatBuoyancy` block the donor does not have") is
correct as a file-shape statement; its premise — that `will_sink` alone is what floats a hull — is
the same name-read as §1, and §3/§4 show the eight floaters also carry a different water tuning, so
`will_sink` 0 alone may not make a Serpente float like the APC.

**Verdict: WEAK.** D-8's choice (lore: sink and stall) is not contradicted — it is what the car
already does under the name-read — but the card's claim that the files *establish* the behaviour, and
therefore that "no water edit is needed", goes a step beyond what is decoded.

---

## What survives, and what should change in the document

**Survives, reproduced to the value:** 232 entities; 189 / 8 / 35; the 35 `BoatBuoyancy` entities
(with `base_buoyancy` 0.1 / 1 / 1.45 and 6 or 9 pontoons); the 8 floaters and their identities; the
10 empty-hull sinkers; the 21 shared constant rows in one `vehicle_common.vmodc` with no override;
the 604 inner files of the build; the donor's 8 `Buoyancy`/`will_sink` values; the 38-path keyword
scan; the 52 module types; the cargo plane's duplicated water modules; the build's water modules
matching the donor on every comparable member (86 of 86, not 8); the `sportsmuscle_body` part
reference (same name and hash in build and cache).

**Does not survive:**
1. **§7/§10's `_ms` unit** — the fleet decodes `_ms` as metres per second in seven sibling members of
   the same shared module; `min/fatal_water_entry_ms` 10/20 are entry-speed thresholds, so the
   "kill side" is a splashdown trigger, not a drown timer (§5);
2. **§3's "will_sink is the only scalar that separates them"** — the eight floaters differ in roll
   damping, reference speed, drag falloff and anti-penetration; the card's own §2 ranges show it
   (§3);
3. **§5's "not because their lift differs"** — the sea scout's lift curve is flat to 1 m/s against
   20 m/s on a sinking helicopter (§4);
4. **§3's "empty hulls still sink"** — circular (§13);
5. **"identical"** for the build's modules and **"triangle mesh"** for the hull — true in the parts
   that are comparable, unverified for the 88-vertex/128-triangle hull and its scale (§10, §11);
6. **the R3 answer** "nothing to change" — the collider is donor-sized baked data and nothing
   compares it with the Batmobile body (§12).

**What the next card should do with this.** WLD-6's decision (D-8 lore: sink and stall) is safe as a
*design* choice. What needs fixing is the evidence trail: relabel the `vehicle_damage.*_water_entry_ms`
rows as water-entry **speed** thresholds in m/s (10 / 20 for sinkers, 20 / 50 for floaters), keep
`engine_shut_down_delay_s` as the only stall member (values 30 / 5), and state plainly that no file
in the fleet expresses drown-at-depth — the one thing the Q-1 probe would settle. The float route's
price should be quoted from the APC's full water tuning (six differing scalars), not from `will_sink`
alone.

**Reproduce.**

```
python Tools/scripts/jc3water.py --check
# census / groups / hulls / part reference: jc3water.load() over the 232 .ee.json caches
# build modules: jc3detail.inner_files + jc3adf.walk on Builds/test-091/…civilian_01.ee
# object graphs: E:/Modding/JustCause3/_grab/detail/*.ee.json (epe.objects[].values keys)
# scripts: E:/Modding/JustCause3/_grab/hud/dec/scripts/hud.as (OXYGEN_DROWNING_THRESHOLD)
```
