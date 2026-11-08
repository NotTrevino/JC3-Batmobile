# Assumption challenge — backlog card B-04 (parts module `sportsmuscle_vehicle_parts.vmodc`)

Scope: `GRAB_BACKLOG.md` §0.5 (R1–R14), the **B-04** card (§8, line 1025), its **§12** row (line
1337), and the B-04 outputs and journal sections: `Tools/scripts/bm_parts.py`,
`Working/Parts/bm_vehicle_parts.json`, `Builds/bm-002/` (`aaf` tree, `.ee`, `.toc`,
`receipt.json`, `verify/`), MODLOG §"B-04 · Parts module — done" (line 16858) and §"B-04 —
re-verified" (line 17083). Where a value is inherited from B-02/B-03/T-12/T-18/T-22, the challenge
follows it to that file, because that is where the assumption really lives.

Read-only: **no file was written except this report**; no game launched, nothing written under
`D:/Games`, no git, no secrets. The card's own Done commands were re-run on the current tree:

```
$ python Tools/scripts/bm_parts.py --check
1. .toc record  sportsmuscle_vehicle_parts.vmodc: offset=16400188 size=39278 (PASS)
2. jc3adf re-read sportsmuscle_vehicle_parts.vmodc: 39278 B, 59 parts, 3915 rows
3. models resolve 59/59 parts; 0 missing .rbm, 0 not packed
4. surviving parts 40 re-read identical: 0 field(s) moved, 4 re-parented ([...])
5. model bytes (distinct .rbm the module references): 8271315 B = 8077.5 KB (222 files); bm-001 7032.4 KB (151 files), delta +1045.1 KB
PASS: Builds/bm-002 re-read (18E55FE4AF78E8E9…, 604 .toc records, 59 parts, 0 problem(s))
EXIT=0
```

It is green. The question is what the green rests on — and, for a parts module, whether "the module
re-reads as written" is even the right question, because a parts module is a table of *behaviour
carriers* (`constraint_index`, behaviour, collision ids, damage type), not a mesh.

## VERDICT summary

| # | Assumption (stated or silent) | Verdict |
|---|---|---|
| B4-01 | "`part_index` is a field, not the array position" — so freeing 1/2 and appending at 42…60 keeps every reference honest | **WEAK** — the *references* are fields, but in **11,643 of 11,643** fleet parts the array position **equals** `part_index`; bm-002 is the first file in the corpus where they diverge, and check step 4 is blind to it by construction |
| B4-02 | A part's `behaviour` (`Turret`/`Cannon`) is the behaviour; the module row is enough for the turret to aim | **BROKEN** — all **24/24** fleet `Turret`+`Cannon` parts (7 Turret, 17 Cannon) ship `constraint_index >= 0` **and** identity `parent_space_offset`; bm-002 writes `constraint_index = -1` **and** a non-identity offset on both, and `TURRET.md` says the hinge *is* the link |
| B4-03 | `hinged_parts` rows carry the flap motion | **BROKEN** — **148/148** fleet `hinged_parts` rows sit on a part with `constraint_index >= 0`; the 4 written rows sit on parts with `-1` |
| B4-04 | Collision ids `-1/-1` are "T-22's hull-less pattern (599/11,643 fleet parts)" and fit the new parts | **BROKEN** — 599 is arithmetically right, but **0/319** fleet Turret/Cannon/AirBrake/GatlingGun/Flaps parts and **14/1,421** `Land_Light` parts are `-1/-1`; `has_world_collision_shape` is 1 on **79/79** weapon-class parts in the sample |
| B4-05 | The 19 parts' `damage_type` values give the intended damage behaviour | **BROKEN** — 3 of the 5 types used are **absent from the host's 24-type `VehicleDamage` table**, so **7/19** parts silently get `Default` (50/30/20) instead of `Land_Generic` (200/0/50) |
| B4-06 | The `ConvertAdf` re-encode (+544 B, +9,392 B total) is padding, not data loss | **HOLDS** — all 544 B land in the data block; type and instance regions are byte-for-byte the same size; no string is lost; 2802/2802 rows re-read (caveat: same decoder on both sides) |
| B4-07 | `rotating_parts.position` = the part's own `parent_space_offset` (claimed "11/11 across 4 modules") | **HOLDS**, and the claim undersells it — **47/47** rotating rows in 22 modules equal their part's offset |
| B4-08 | `number_of_blades` 1 for the gatling | **HOLDS** (6/6 fleet gatling rows are 1) but is **uninformative**: 1 is also the `RotatingPart` type default |
| B4-09 | `rotation_axis` (0, 0, −1) from T-12's `joint.axis_jc3` is the axis the game spins on | **WEAK** — it is the correct R2 rotation of the BmAK +X joint axis, but **6/6** shipped gatling rows use **+Z**, and the frame (part-local vs parent) is not established |
| B4-10 | `aim_part_constraints` = 0 because "the turret aim is not a module array" (a no-carrier claim) | **WEAK** — the negative reproduces (85 rows / 17 modules, 0 naming a Turret or Cannon part) but over **79 of 233** modules, and `TURRET.md` itself names the real carrier, which bm-002 does not write |
| B4-11 | `parent_space_offset` = pivot, i.e. the two frames in play (pivot-local parts, body-space lamps) are the right ones | **HOLDS** — measured: 15 parts pivot-local (AABB centre near origin), 4 lamps body-space with offset 0, same dual convention as the donor's own parts |
| B4-12 | The 4 wheel-arch lamps may be parented to the **wheel** parts | **WEAK** — **0 of 669** fleet `has_lights = 1` parts are children of a `Wheel` part; B-03 §B10 already flags 594/612 of that lamp's faces coming from a damper bone |
| B4-13 | `is_deformable` 0 on all 19 parts | **WEAK** — 16/22 fleet **Turret** parts ship `is_deformable = 1`; the card dictates 0 |
| B4-14 | The 19 hand-written `.lod` files are "the vanilla layout (LOD list, blank slots, trailing 1.0)" | **BROKEN for the 8 lamp files** — every shipped 3-LOD `.lod` in the donor build (8/8) is `path, path, path, -, -, value`; the 8 written files are `path, path, path, value` |
| B4-15 | R9's model budget is green (4,899.6 of 4,915 KB) | **WEAK** — bm-002 measures **8,077.5 KB of 4,915** and the receipt says so; the green figure is B-02/B-03 accounting for a body/wheel re-emit that has not happened |
| B4-16 | The card's Done gate re-reads the **built** module | **BROKEN** — `jc3parts.py check` reads `ENTITIES.md`'s donor table + `Working/Translation/current.json`, and printed "donor table has 42 parts"; it cannot see the 59-part build |
| B4-17 | Removing the two door parts leaves no reference behind | **WEAK** — stated for the deform module (16 points), **unstated** for the `.epe`: two `CInteractionGraphExit` objects still name `sportsmuscle_door_f_l` / `_f_r` |
| B4-18 | Re-parenting the 4 orphans to the body is transform-neutral and harmless | **HOLDS** on transform (all four, and both doors, ship identity offsets); **WEAK** on consequence — nothing hides the door glass and mirrors, which still render |
| B4-19 | Every part's model resolves | **HOLDS** — 59/59 paths exist **and** 59/59 stored hashes equal `hash_jenkins(path)` |

Overall: the **edit mechanics** of B-04 are solid.The
re-encode is provably structure-preserving
(B4-06), the surviving records spot-checked (body, 4 wheels, taillight, 4 orphans) carry their
shipped values, the model hashes and the `.toc` record are right (B4-19), and the two fleet rules the card leans on hardest turn out to
be *stronger* than claimed (`rotating_parts.position`, 47/47 not 11/11). What does **not** hold is
the part of the row that is behaviour: the new parts carry behaviour **names** whose carriers —
`constraint_index` → a `.physicsc` hinge, collision ids, an in-table damage type, and a `.lod`
layout — are all set to values that no shipped part of the same class uses (B4-02, -03, -04, -05,
-14). In R5's terms the turret, cannon, gatling, suppressor and flaps are currently *members*, not
behaviours. Two further things are wrong with the record rather than the file: the Done gate that
closed the card reads the donor, not the build (B4-16), and the budget it reports is an accounting
figure while the tree on disk is 3,162.5 KB over the hard wall (B4-15).

---

## B4-01 · "`part_index` is a field, not the array position"

**The assumption (stated, in the spec).** `Working/Parts/bm_vehicle_parts.json` `index_map.note`:
"`part_index` is a field, not the array position: the surviving records keep their shipped indices
(so 1 and 2 are now free) and every reference (`parent_part_index`, `children_part_indices`,
`wheel_parts`, `door_parts`) keeps its meaning." The MODLOG adds: "`part_index` is a field, not the
array position, so every other index and reference keeps its meaning; 1 and 2 are simply free now."

**Why it matters.** If the engine (or any consumer) walks `parts[i]` and expects part `i`, the whole
module shifts by one after the first hole: every part after the body would render, deform and take
damage as its neighbour. The alternative edit — remove and *renumber* — keeps `position == index`
and cannot have this failure mode at all.

**Test 1 — does the fleet ever store the array out of index order?**

```
$ python (walk Research/JC3Grab/PARTS_TABLE.jsonl: array position vs parts[].i)
fleet PARTS_TABLE: 11643 parts, 0 whose array position != part_index, in 0 entities
```

**Test 2 — what bm-002 does.**

```
$ python (jc3adf walk of Builds/bm-002/…/sportsmuscle_vehicle_parts.vmodc)
  bm-002 array position 0 part_index 0 sportsmuscle_body
  bm-002 array position 1 part_index 3 sportsmuscle_engine
  bm-002 array position 2 part_index 4 sportsmuscle_f_l_seat
  bm-002 array position 3 part_index 5 sportsmuscle_f_r_seat
```

**Test 3 — can the card's check see it?** Check step 4 compares the surviving parts "field for
field" through `jc3adf.parts()`, which reads `part_index` **by name**. A build where every record
is off by one array slot re-reads as "0 field(s) moved" by construction.

```
$ python (every part-index-like member of the built module, values 1 and 2)
references to 1 or 2 anywhere in the built parts module: 0
body kids: [[3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]]
part count 59
```

The cleanup inside the module is complete (the body's 15 kids lost 1 and 2 and no member names
them). The 16 references that remain are outside it, in the deform module — B4-17.

The references that *are* fields are genuinely fields (the `.epe`'s 6 `CPartProp` nodes carry
`part_index` 0, 11, 12, 26, 27, 8 by value; the lights module carries `part_index` 8 twice for two
entries on part 8). So the field reading is right. The problem is the other direction: nothing on
disk shows the engine tolerating a **gap** in the array, and the corpus offers no precedent
(0/11,643).

**Verdict: WEAK.** The reference semantics are supported; the "array may be out of order" half is
an inference with zero shipped precedent and is not covered by the check that closed the card. A
1-line experiment settles it (`index_map` keeps 1/2 free; a control build that renumbers so
`position == index` for all 59 parts is byte-different but semantically equal on every field the
card checked) — see "what would settle it" below.

## B4-02 · A part's `behaviour` name is the behaviour (turret and cannon)

**The assumption (stated, §12/MODLOG).** "`rotating_parts` 1 (Vulcan …), `door_parts` = [25] only,
`aim_part_constraints` 0 (G2-13: all suspension)" and, for the turret/cannon/suppressor, "damage
types and behaviours from T-12". The rows are written with `behavior` `Turret`/`Cannon` and nothing
else.

**Why it matters.** This is R5 stated exactly ("behaviour before member … not by the JC3 member
whose name sounds closest"). `Research/JC3Grab/TURRET.md` line 3: "The yaw part carries behaviour
`Turret`, the pitch part carries behaviour `Cannon`, **each is one
`hkpLimitedHingeConstraintData` in the vehicle's `.physicsc`**"; §4: "for a tank the hinge is not
declared in the parts module at all — the part's `constraint_index` points into `.physicsc`, and
**that is the whole link**".

**Test — census every `Turret`/`Cannon`/`AirBrake`/`GatlingGun` part in the 80 locally cached parts
modules (`E:/Modding/JustCause3/_grab/tmp|probe/*_vehicle_parts.vmodc`, decoded with `jc3adf`), then read
the same fields out of bm-002.**

```
Turret/Cannon/AirBrake/GatlingGun parts (80 modules): 31
    ('advancedassault_vehicle_parts.vmodc', 7, 'Cannon', 11, 'identity', [0,0,0], 'advancedassault_gatling_l_mount')
    ('apc_vehicle_parts.vmodc', 30, 'Turret', 15, 'identity', [0,0,0], 'apc_turret_base')
    ('mediumtank_vehicle_parts.vmodc', 26, 'Turret', 2, 'identity', [0,0,0], 'mediumtank_turret')
    ('mediumtank_vehicle_parts.vmodc', 38, 'Cannon', 0, 'identity', [0,0,0], 'mediumtank_cannon')
    ('smalltank_vehicle_parts.vmodc', 10, 'Turret', 16, 'identity', [0,0,0], 'smalltank_turret')
    … 24 Turret+Cannon parts in all (7 Turret, 17 Cannon), every one constraint_index >= 0 and offset [0,0,0]
```

```
$ python (built module, tmp/b04/build/bm_vehicle_parts.xml)
batmobile_turret          ci= -1 | body= -1 ray= -1
     pso= ['1','0','0','0','0','1','0','0','0','0','1','0','1.3e-05','0.876249','0.333226','1'] beh= ('Turret', 3933508936)
batmobile_cannon          ci= -1
     pso= ['1',…,'0.000345','0.826197','-0.31564','1'] beh= ('Cannon', 2848129780)
```

```
$ python (bm-002 physicsc string census)
sportsmuscle.physicsc 340368 B
    hkpLimitedHingeConstraintData 1        (the type name; no part is named)
    batmobile_turret 0   batmobile_cannon 0   batmobile_airbrake/aero 0
```

**Result.** The build has the name, not the link: `constraint_index = -1` on 19/19 new parts, and
the module's own `parent_space_offset` now carries the placement that in the fleet is carried by the
hinge pivot (0.876 m up, 0.333 m back for the turret). So the turret will not yaw, and when B-05
adds a hinge at the tank-like pivot it will also have to decide which of the two placements is
authoritative.

**Verdict: BROKEN** (R5). The parts module row for a `Turret` part in JC3 is a pointer into
`.physicsc`; the pointer is `-1`. The card's own spec text is not wrong — it correctly refuses to
invent an `aim_part_constraints` row — but it treats "no aim row needed" as "nothing else needed",
and the thing that is needed (`constraint_index`, and the hinge/pivot pair) is absent.

## B4-03 · `hinged_parts` rows carry the flap motion

**The assumption (stated).** "behaviour rows: `hinged_parts` 4 rows (the AirBrake flaps, T-12
channel `hinged`)"; the spec's `hinged_parts.source` is "T-12 rows with `behaviour_channel: hinged`
(AirBrake)".

**Test — the fleet's own `hinged_parts` convention, all 148 rows in the 80 cached modules, joined to
the part's `constraint_index`.**

```
  hinged rows total: 148
    ('LandingGear', 'ci>=0') 22
    ('LandingGearHatch', 'ci>=0') 19
    ('Flaps', 'ci>=0') 48
    ('SteeringFork', 'ci>=0') 11
    ('Elevator', 'ci>=0') 12
    ('LeftAileron', 'ci>=0') 6
    ('RightAileron', 'ci>=0') 6
    ('Rudder', 'ci>=0') 10
    ('AirBrake', 'ci>=0') 1
    ('BoatEngine', 'ci>=0') 13
```

148 of 148 — including the one shipped `AirBrake` part (`fighterbomber_airbrake`, part 12,
`constraint_index` 3, offset `[0,0,0]`). bm-002's `hedged_parts` = `[56, 57, 58, 59]` on parts with
`constraint_index = -1` and non-identity offsets.

**Verdict: BROKEN**, same mechanism as B4-02: `HingedPart` is a one-member struct (`part_index`
only, verified from the type definition), so the array is a list of *pointers into the hinge table*,
not a hinge declaration. Adding the pointer without the hinge makes four inert rows.

## B4-04 · Collision ids `-1/-1` are the hull-less pattern and fit these parts

**The assumption (stated, in every one of the 19 rows).** `collision_source`: "t16_collision.json
(T-22) bindings: a part with no hull is world_collision_body_id -1; **599/11643 fleet parts** ship
body -1 / ray -1", plus `has_world_collision_shape = 0`.

**Test 1 — is 599 right?**

```
parts 11643
body==-1 and ray==-1: 599      body==-1: 761      ray==-1: 599
mixed body/ray -1: 162   (e.g. armoredtruck_wheel_f_l  body -1  ray 52)
```

599 reproduces exactly. **Test 2 — who are the 599?** Join to behaviour and damage type:

```
  behaviour Turret: 22 parts, {'has ids': 22}
  behaviour Cannon: 68 parts, {'has ids': 68}
  behaviour AirBrake: 3 parts, {'has ids': 3}
  behaviour GatlingGun: 24 parts, {'has ids': 24}
  behaviour Flaps: 202 parts, {'has ids': 202}
fleet Land_Light parts: 1421 {'has ids': 1407, '-1/-1': 14}
```

**Test 3 — the flag itself, in the sample that decodes it:**

```
behaviour, has_world_collision_shape, is_deformable -> count
   ('AirBrake', 1, 0) 1
   ('Cannon', 1, 0) 15     ('Cannon', 1, 1) 2
   ('Flaps', 1, 0) 44      ('Flaps', 1, 1) 4
   ('GatlingGun', 1, 0) 6
   ('Turret', 1, 0) 2      ('Turret', 1, 1) 5
Land_Light: (1,id) 450, (0,-1) 6
```

**Result.** The number the row cites is real, and it describes a population (hull-less decorative
parts) that contains **none** of the classes B-04 dresses in it: 319/319 weapon/flap parts and
1,407/1,421 lamp parts in the fleet carry collision ids, and 79/79 weapon-class parts in the sample
carry `has_world_collision_shape = 1`. B-10 wrote 5 hulls for body+wheels and correctly left the
new parts alone — so the stat is being used for a decision it does not support.

**Verdict: BROKEN.** A fleet count was taken as a licence; the same corpus, cut by the same
behaviours, says the opposite (0%). Consequence: the turret, cannon, gatling, suppressor, pods,
flaps and lamps are not hit-testable as parts and, per T-22's binding, cannot take part damage even
though B4-05 gives them damage types.

## B4-05 · The 19 parts' `damage_type` values give the intended damage behaviour

**The assumption (stated).** Each row cites `damage_type_source` "T-12 P-xx `damage_type`
(land-first)". Values used: `Land_Light` ×8, `Land_Generic` ×4, `Plane_Control_Surface` ×4,
`Train_Generic` ×2, `Boat_Generic` ×1.

**Test — read the host entity's `VehicleDamage` module (`lave_health_medium.vmodc`, the file the
`.epe` `damage` reference points at) and look up each type.**

```
$ python (E:/Modding/JustCause3/_grab/entities/*sportsmuscle_civilian_01.ee.json, module VehicleDamage)
n part damage types: 24
type                      initial_health  damaged_health   loosen_health  instantly_damaged
Default                               50              30              20                0
Land_Generic                         200               0              50                0
Land_Light                            50              30              20                1
…
Boat_Generic in table: False
Train_Generic in table: False
Plane_Control_Surface in table: False
Boat_Antenna in table: False
```

**Result.** The 24-type table is land-only. **7 of 19** new parts name a type that is not in it —
the machine gun (`Boat_Generic`), both missile pods (`Train_Generic`), all four flaps
(`Plane_Control_Surface`) — so they fall back to `Default`: 50/30/20 instead of 200/0/50, a
different loosen threshold and a different damage ladder. That is not an aesthetic difference; it is
the ARM-4 row the card claims to serve. The `jc3parts.py check` note that the card quotes only
mentions `Boat_Antenna`, and it is about the **donor's** 42 parts, not the 19 new ones:

```
$ python Tools/scripts/jc3parts.py check
ok: 40 part indices agree between .epe and DeformPoints; 4 wheel points -> 4 wheel parts; 21 light points -> 12 parts
ok: donor table has 42 parts, names 42/42 with DeformPoints, lights 12 parts match, wheels 4 match, damage types 17 used
  note: ['Boat_Antenna'] not in this vehicle's VehicleDamage table (24 types) - the part falls back to Default damage
```

**Verdict: BROKEN.** The types are members of a 71-value fleet vocabulary (`PARTS_TABLE.jsonl`) and
were copied without checking them against the one table that will consume them. `Boat_Antenna` —
already flagged by the tool — is not even one of the 19.

## B4-06 · The `ConvertAdf` re-encode is padding, not data loss

**The assumption (stated, and load-bearing).** "the +544 B is placement padding, not data loss …
2802/2802 rows and 42/42 parts identical, 29,886 → 30,430 B." Everything else in the card rides on
this: if the writer drops or reorders a member the old reader does not model, the "40 re-read
identical" check is a check of the decoder against itself.

**Test — compare the original module and the unchanged round trip at the container level, not the
decoded level.**

```
$ python (header fields of tmp/b04/base.vmodc vs tmp/b04/rt.vmodc)
size       base=   29886 rt=   30430  delta=544
data_end   base=   23920 rt=   24464  delta=544
n_types    base=      31 rt=      31  delta=0
types_off  base=   23944 rt=   24488  delta=544
n_inst     base=     106 rt=     106  delta=0
inst_off   base=   28096 rt=   28640  delta=544
inst_end   base=   29886 rt=   30430  delta=544
```

Instance region: 29886−28096 = **1790**; 30430−28640 = **1790**. Type region: 4152 both. So the
whole delta is in the data block (strings + inline data), and the per-member layout of the instance
did not grow or shrink by a single byte — a dropped member would show up here. String census:

```
strings base 258 (248 unique)   rt 287 (250 unique)
only in base: []
only in rt:   ['?e3V', '?e3V?']      (binary matched as text, not strings)
```

No string lost; the writer *duplicates* rather than shares them (37 repeated matches vs 10), which
is where the 544 B comes from.

**Verdict: HOLDS.** The caveat belongs in the record, not as a doubt: both readings are the same
reader, so a member that `jc3adf` does not model at all would be invisible twice — but the
container-level equality of the instance region rules out the specific failure the card worries
about (a member silently dropped by the writer). Phase Q is still the only test of the game's
acceptance, as the card says.

## B4-07 · `rotating_parts.position` equals the part's own `parent_space_offset`

**The assumption (stated, and the only one with a stated sample size).** Spec
`rotating_parts.rows[0].position_source`: "decoded (fleet): equals the part's own
`parent_space_offset` translation in **11/11** shipped rotating rows sampled across **4** modules";
MODLOG: "the rule holds in 11/11 shipped rotating rows across four modules".

**Test — decode all 80 cached parts modules and compare every `rotating_parts[k].position` with the
`parent_space_offset` translation of the part it names.**

```
modules on disk: 80      decoded ok: 80      failed: []
ROTATING rows total: 47
  position==part pso: 47   disagree: 0   missing part: 0
  rows per module: advancedassault 3, assault 2, cargotransport 4, corvette 5, heavyassault 2,
                   heavytroop 2, lightassault 4, lightpatrol 2, mediumoldfishing 1, motoryacht 2,
                   oldtractor 1, oldtruck 1, privatepropeller 2, racingboat 4, sailboat 1,
                   seascout 2, smallfloatprop 1, smalloldfishing 1, spyspeedboat 2, transport 2,
                   utility 2, vintagefighter 1
```

**Verdict: HOLDS — and the card understates it.** 47/47 across 22 modules, not 11/11 across 4. The
value written for `batmobile_machine_gun` (−0.091673 / 0.536892 / 0.476501) is its own offset and is
in exactly the right relation to the module.

## B4-08 · `number_of_blades` = 1 for a gatling

**The assumption (stated).** "`number_of_blades` 1 from the fleet's own gatling rows"; source
string: "`advancedassault_gatling_l_barrels` / `_r_barrels` ship number_of_blades 1".

**Test — every gatling rotating row in the 80 modules, with its axis and rpm members.**

```
advancedassault_vehicle_parts.vmod  i= 39 blades=1 axis=[0.0, 0.0, 1.0] pos=[-1.175, 1.26, -0.094] rpm_mult=1.0 min_rpm=-1.0 max_rpm=-1.0 trans=-1.0
advancedassault_vehicle_parts.vmod  i= 40 blades=1 axis=[0.0, 0.0, 1.0] pos=[1.175, 1.26, -0.094]  …
lightassault_vehicle_parts.vmodc    i= 42 blades=1 axis=[0.0, 0.0, 1.0] …
lightassault_vehicle_parts.vmodc    i= 43 blades=1 axis=[0.0, 0.0, 1.0] …
racingboat_vehicle_parts.vmodc      i= 21 blades=1 axis=[0.0, 0.0, 1.0] …
racingboat_vehicle_parts.vmodc      i= 22 blades=1 axis=[0.0, 0.0, 1.0] …
```

**Result.** 6/6 gatling rows are `1`, and all four rpm members are `1.0 / −1.0 / −1.0 / −1.0` in
all 47 fleet rows — exactly what B-04 wrote. But the `RotatingPart` type definition declares
`number_of_blades` with `size 1, default 1`: writing 1 is writing the default, so the fleet evidence
and the omission are the same bytes. It is right and it carries no information.

**Verdict: HOLDS (as a value), uninformative (as provenance).** Nothing to fix; the source string
should say "type default, corroborated by 6/6 gatling rows" rather than implying a decoded count.

## B4-09 · `rotation_axis` (0, 0, −1) is the axis the game spins the barrels on

**The assumption (stated).** `rotation_axis_source`: "T-12 P-03 `joint.axis_jc3`". The T-12 joint
carries `axis_local: "+X"` (BmAK), `axis_jc3: [-0.0, 0.0, -1.0]`, `axis_world_jc3: [0.0, -0.0001,
-1.0]`.

**Test 1 — is the −Z the correct image of +X under R2?** `bat_assemble.to_jc3_rot`: "PSK (X length
prow+, Y width, Z up) -> JC3 (X width, Y up, Z length, front −Z) as a **proper** rotation (det +1):
(−y, z, −x)". The image of (1, 0, 0) is (0, 0, −1). Correct.

**Test 2 — what do shipped gatlings write?** From the table above: **6/6 use (0, 0, +1)**, i.e. the
opposite sign to bm-002, and the same axis line. The `RotatingPart` type's `rotation_axis` default
is the bit pattern 1922527373 = 5.999e30 as a float (i.e. not an axis at all), so the fleet's
(0, 0, 1) is authored data, not a default.

**Result.** Two readings are possible and the files do not separate them: (a) the field is a
direction in the part's own frame and +Z is "out of the barrel" for a mount whose pivot faces
backwards; (b) the field is in parent space and the sign only sets spin direction. Nothing in
`PARTS_TABLE.jsonl`, `TURRET.md` or the module decodes the frame of `rotation_axis`, and the card's
own provenance chain ends at T-12's *transformed bone axis*, which is a world direction, not a
part-local one. For a 1-bladed "blade" the visual difference is the spin direction of an
axisymmetric cluster — cosmetic — but it is also unverified.

**Verdict: WEAK.** Direction and magnitude are right (the barrels' own bone turns about it); the
sign contradicts 6/6 shipped rows and the frame is UNKNOWN. Cheap test: the same value with +Z in
one build and compare the two in phase Q, one variable per probe (R13).

## B4-10 · `aim_part_constraints` = 0 because nothing carries turret aim in the parts module

**The assumption (stated).** `aim_part_constraints.source`: "G2-13 …: `aim_part_constraints` = 85
rows in 17 of 78 modules, all suspension, **0 on the six turreted vehicles** — so the turret/cannon
aim is not a module array and no row is written".

**Test — re-run the census over every parts module on disk and join both sides of every row to the
part's behaviour.**

```
modules: 79 (unique names; 80 files)
aim rows total: 85 in 17 modules
aim rows naming a Turret/Cannon part: 0 []
aim behaviour pairs:
    ('None', 'BrakeDrum') 28   ('None', 'Wheel') 14   ('None', 'BrakeDisc') 12
    ('None', 'None') 10        ('Spring', 'Wheel') 5  ('None', 'BrakeCalipers') 4
    ('Spring', 'BrakeDrum') 4  …
```

**Result.** The numbers reproduce exactly (85/17/0). Two limits belong in the record: (i)
`TURRET.md` §Limits says it itself — "The `aim_part_constraints` census covers the modules in the
local cache, **not all 233**" — so the "no carrier" statement is a 79-of-233 sample, and the 154
uncached modules are exactly the ones whose parts table `PARTS_TABLE.jsonl` *does* cover but whose
arrays are not decoded; (ii) the negative is true but answers the wrong question: the carrier G2-13
found is `constraint_index` → hinge (B4-02), which is not an array at all.

**Verdict: WEAK** as an exhaustive claim; the *decision not to invent a row* is right. The document
it cites contradicts the "complete" reading by its own admission, and the decision it supports
(no aim row) is unrelated to the missing link (no hinge).

## B4-11 · `parent_space_offset` = pivot, and the two frames in play are the right ones

**The assumption (stated).** Every row: `parent_space_offset` "derived: B-02/B-03 pivot_m − the
parent part's frame origin chained from this module's `parent_space_offset`". Silently this asserts
that (a) geometry is emitted **in the parent's frame** (pivot-local), and (b) for the six lamps
whose manifest pivot is `[0,0,0]` the geometry is in **body** space, so offset 0 is right.

**Test — read each part's LOD1 AABB from its own RBM header (`rbmhdr.read_header`) and compare the
centre with the offset the module stores.**

```
part                           pso                          lod1 AABB centre           centre-pso
sportsmuscle_headlight_f_l     [0.0, 0.0, 0.0]              [-0.417, 0.612, -3.007]    [-0.417, 0.612, -3.007]
sportsmuscle_tailstrip_r_l     [0.0, 0.0, 0.0]              [-1.295, 0.726, 3.298]     [-1.295, 0.726, 3.298]
batmobile_turret               [0.0, 0.876, 0.333]          [0.001, 0.472, 0.041]      [0.001, -0.404, -0.293]
batmobile_cannon               [0.0, 0.826, -0.316]         [-0.001, 0.024, -0.188]    [-0.001, -0.802, 0.128]
batmobile_machine_gun          [-0.092, 0.537, 0.477]       [-0.102, 0.139, -0.185]    [-0.01, -0.398, -0.661]
batmobile_jet                  [0.0, 0.543, 1.343]          [-0.0, 0.003, 1.401]       [-0.0, -0.54, 0.058]
sportsmuscle_wheel_f_l_arch    [-0.323, 0.305, -1.013]      [-0.0, 0.298, -0.404]      [0.323, -0.007, 0.608]
```

and the donor's own parts show the same split:

```
sportsmuscle_wheel_f_l   pso=[-0.885, 0.4, -1.557]  AABB centre [0.163, 0.016, -0.0]   (pivot-local)
sportsmuscle_body        pso=[0.0, 0.0, 0.0]        AABB centre [-0.002, 1.225, 0.092] (body-space)
sportsmuscle_taillight_r_l pso=[0,0,0]  centroid=[-0.6862, 0.8302, 2.2986]  AABB centre [-0.686, 0.830, 2.299]
```

**Result.** The rule is consistent and self-checking: 15 parts (the 11 cut parts and the 4 arch
lamps) are pivot-local — centre within the part's own half-extent of the origin — and 4 lamps
(2 headlights, 2 tailstrips) are body-space with offset 0, which is precisely the donor's dual
convention (wheels pivot-local, body/taillight body-space, with `centroid` equal to
the AABB centre where the geometry is body-space). A sign or axis error would put these centres a
car-length away; none does.

**Verdict: HOLDS.** (The *choice* of parent for four of the lamps is a separate matter — B4-12.)

## B4-12 · The four wheel-arch lamps may be parented to the wheel parts

**The assumption (silent, inherited).** B-03's manifest sets `parent: 26` (`wheel_f_l`) for
`sportsmuscle_wheel_f_l_arch`, and B-04 chains the offset through the wheel's own `parent_space_offset`
("parent: sportsmuscle_wheel_f_l, parent_index 26"). Nothing in the card discusses what happens when
a part hangs on a wheel.

**Test 1 — is there a fleet precedent for a lit part under a wheel?**

```
has_lights=1 parts whose parent behaviour is Wheel: 0 []      (669 lit parts, 79 modules)
```

**Test 2 — where does the lamp actually sit, and what geometry is it?** From B-03's own manifest
(not re-derived here):

```
sportsmuscle_wheel_f_l_arch: pivot_m [-1.208, 0.7047, -2.5699]
  bbox_body_m  x -1.2708..-1.1452   y 0.7436..1.2617   z -3.1375..-2.8111
  bones: [["Damper_Left_Front_02", 594], ["Wheel_Frnt_Left_Disc", 18]]   faces_lod0 612
```

The front wheel's pivot is `(-0.885, 0.400, -1.557)` with tyre Ø1.366 m, i.e. the tyre spans
z −2.24 … −0.88. The lamp sits at z −3.14 … −2.81 — **0.57 m ahead of the tyre's leading edge**, on
the fender, not in the arch. B-03's own challenge report records the same thing as its §B10
("594/612 faces on `Damper_Left_Front_02` but parented to the wheel").

**Result.** Both halves are inherited, but B-04 is where they become a *transform*: the part's
placement is now expressed relative to the wheel's hub, so any wheel motion (spin, steer, suspension
travel carried by the part rather than the physics) moves the lamp. There is no shipped example of a
lit part parented to a wheel (0/669), so there is no evidence the engine expects it.

**Verdict: WEAK.** Not a B-04 arithmetic error — the chaining rule is applied correctly to a
questionably chosen parent — but it is an assumption the card's result rests on and it rests on
nothing.

## B4-13 · `is_deformable` 0 on all 19 parts

**The assumption (from the card itself).** Card step 2: "`is_deformable` 0"; every row cites "B-04
card".

**Test — the fleet's flag for the same behaviours.**

```
deform flag by behaviour Turret {0: 6, 1: 16}
deform flag by behaviour Cannon {0: 62, 1: 6}
deform flag by behaviour AirBrake {0: 3}
deform flag by behaviour GatlingGun {0: 24}
deform flag by behaviour Flaps {0: 190, 1: 12}
```

**Verdict: WEAK.** For the cannon, gatling, flaps and lamps 0 is the fleet norm, so the card's
blanket rule is right for 18 of 19 parts. For the **turret** the majority (16/22) is deformable — the
turret is the one part built to absorb a hit and stay attached. The card's uniform 0 is a
simplification, not decoded, and the parts module feeds `sportsmuscle_vehicle_deform.vmodc` (which
B-04 leaves naming parts 1/2 anyway — B4-17).

## B4-14 · The 19 hand-written `.lod` files are "the vanilla layout (LOD list, blank slots, trailing 1.0)"

**The assumption (stated, MODLOG limit 5).** "19 `.lod` written in the vanilla layout (LOD list,
blank slots, trailing `1.0`)".

**Test — classify every `.lod` in bm-001 (shipped) and bm-002 by its line pattern.**

```
Builds/bm-001/aaf lod files 59
   rbms=5 tail=('1.0',) : 43
   rbms=3 tail=('-', '-', '1.0') : 6
   rbms=4 tail=('-', '1.79999995232') : 4
   rbms=3 tail=('-', '-', '0.800000011921') : 2
   rbms=4 tail=('-', '0.600000023842') : 2
   rbms=4 tail=('-', '0.899999976158') : 2
Builds/bm-002/aaf lod files 78
   rbms=5 tail=('1.0',) : 54          (= 43 shipped + 11 written)
   rbms=3 tail=('1.0',) : 8           (= 8 written by B-04)  <-- no placeholder
   rbms=3 tail=('-', '-', '1.0') : 6
   …
```

Concretely, one shipped 3-LOD file and one written 3-LOD file:

```
== Builds/bm-001/aaf  sportsmuscle_headlight_f_l_02mshswap.lod
    'sportsmuscle_headlight_f_l_02mshswap_lod1.rbm'
    'sportsmuscle_headlight_f_l_02mshswap_lod2.rbm'
    'sportsmuscle_headlight_f_l_02mshswap_lod3.rbm'
    '-'    '-'
    '1.0'
== Builds/bm-002/aaf  sportsmuscle_headlight_f_l.lod
    'sportsmuscle_headlight_f_l_lod1.rbm'
    'sportsmuscle_headlight_f_l_lod2.rbm'
    'sportsmuscle_headlight_f_l_lod3.rbm'
    '1.0'
```

**Result.** The 11 five-LOD files reproduce the shipped five-LOD form byte-pattern for byte-pattern
(43/43 shipped are `path×5, 1.0`). The **8** three-LOD lamp files do not: every shipped three-LOD
`.lod` in the donor (8/8, including four `*mshswap` headlights and the taillight-family parts) has
one `-` per unused slot before the value; none of the written files does, and the claim that the
written files contain "blank slots" is false (0/19 do). If the reader walks slots positionally,
`1.0` is read as the value of the *first* slot and LOD2/LOD3 fall off the list.

**Verdict: BROKEN for the 8 lamp files** — the one artefact class the card had to author from a
pattern was authored from the wrong pattern, and the record describes the wrong pattern. The 11
five-LOD files are fine.

## B4-15 · R9's model budget is green

**The assumption (stated, MODLOG limit 2).** "the build reports model bytes as a delta (+1,045.1 KB
over bm-001 …) and quotes B-02's 4,790.9 KB / B-03's net 4,899.6 of 4,915 KB as the figures that
apply once the re-emit lands."

**Test 1 — the build's own number.**

```
$ python Tools/scripts/bm_parts.py --check
5. model bytes (distinct .rbm the module references): 8271315 B = 8077.5 KB (222 files); bm-001 7032.4 KB (151 files), delta +1045.1 KB
$ python -c "print(json.load(open('Builds/bm-002/receipt.json'))['budgets'])"
{'model_kb': 8077.456, 'model_cap_kb': 4915.0, 'model_files': 222, 'base_model_kb': 7032.369,
 'delta_kb': 1045.087, 'textures_added': 0, 'note': '… R9 is reported as the delta against bm-001
 and stays open until that re-emit lands. …'}
```

**Test 2 — how much of it is the appearance set, by the files actually on disk** (naive stem join,
so ±1% and not the tool's 222/8,077.5, but it shows the shape):

```
{'new19': (103 files, 1491.3 KB), 'body': (5, 3405.8), 'wheels4': (20, 1358.4), 'other-shipped': (110, 2015.2)}
```

body + wheels + the 19 new parts ≈ **6,255.5 KB** — i.e. even after removing the 2,015 KB of shipped
Serpente parts that B-02 will replace, the set is **27 % over the 4,915 KB wall**, and the 4,899.6
KB figure is arithmetic on B-02's and B-03's re-emitted meshes, not a property of this tree.

**Verdict: WEAK** — and the honest part of the record survives: the receipt calls R9 **open**, does
not claim green, and `bm_parts.py` reports the cap next to the number. What is weak is the sentence
in the journal, which reads as "4,899.6 applies" when nothing on disk measures it, and the fact that
B-04 is `done` while its own build is 3,162.5 KB over a hard wall (R9: "Over budget = the whole
entity vanishes"), with the overage attributed to a *third* card that no task currently owns.

## B4-16 · The card's Done gate re-reads the built module

**The assumption (stated in the Done line).** "Done: `jc3parts.py check` and `jc3adf.py` re-read the
built module; every part's model resolves to a file in the build".

**Test — what `jc3parts.py check` actually opens.**

```
$ grep -n "def epe_parts" -A 3 Tools/scripts/jc3parts.py
117:def epe_parts() -> dict[int, str]:
118-    """Donor part table out of ENTITIES.md ('Donor parts' section)."""
…
$ grep -n "def deform_parts" -A 3 Tools/scripts/jc3parts.py
140:def deform_parts() -> dict[int, str]:
141-    """Part index -> name from the build's own DeformPoints module."""
142-    vals = deform_values()          # <- Working/Translation/current.json (the donor snapshot)
$ grep -n "donor = None" -A 4 Tools/scripts/jc3parts.py
344:    donor = None
345-    with open(table, …) as f:
347-            row = json.loads(line)
348-            if "v0300_car_kensington_sportsmuscle_civilian_01" in row["entity"]:
349-                donor = row
```

and its own output says so: "**donor table has 42 parts**". Nothing in the tool names `Builds/`.

**Result.** Of the card's three Done checks, one (`bm_parts.py --check`) genuinely re-reads the
build, and it is strong; `jc3adf.py dump` reads the build but only prints; `jc3parts.py check` reads
the donor and cannot fail on any of the 19 new parts — which is exactly why B4-04 and B4-05 went
unnoticed (the types and collision ids of the new rows are invisible to it).

**Verdict: BROKEN** as a verification claim. The card is `done` on a gate that inspects the wrong
file for two of its three items.

## B4-17 · Removing the two door parts leaves no reference behind

**The assumption (partly stated).** MODLOG limit 3: "`sportsmuscle_vehicle_deform.vmodc` still names
parts 1 and 2 as deform targets … the card edits the parts module only". Nothing is said about the
entity graph.

**Test 1 — the deform module.**

```
deform part_index rows 270
references to index 1: 8   index 2: 8
    points[2].from_part_index = 1      points[2].skinned_to_part_index = 1
    points[14].from_part_index = 1     points[16].from_part_index = 1 …
```

**Test 2 — the `.epe`.** Exported graph (`tmp/b05/base.xml`, B-05's export of bm-002's `.epe`) still
contains both removed names, inside the driver's exit animation object:

```
$ python (CPartProp census of the .epe + string scan)
occurrences sportsmuscle_door: ['sportsmuscle_door_f_l', 'sportsmuscle_door_f_r']
CPartProp count 6  [('sportsmuscle_body','0'), ('sportsmuscle_wheel_r_r','12'), ('sportsmuscle_wheel_r_l','11'),
                    ('sportsmuscle_wheel_f_r','27'), ('sportsmuscle_wheel_f_l','26'), ('sportsmuscle_taillight_r_l','8')]
…
<object id="1481278F">
  <value name="_class" type="string">CInteractionGraphExit</value>
  <value name="name" type="string">exit.ai.driver.default</value>
  <value name="state" type="string">S_EXIT_VEHICLE</value>
  <value id="85CEE196" type="string">sportsmuscle_door_f_l</value>
```

The `.epe` does carry a `entry.driver.no.door` variant, so entry is covered; **exit** still names the
door part it animates, on both sides.

**Verdict: WEAK.** The deform side is stated and has a size now (16 points). The `.epe` side is a
real dangling reference, it is the *same class* of leftover, and it is absent from the limits list —
B-05's card owns the graph, but B-04's "out" claims the module set is complete.

## B4-18 · Re-parenting the four orphans to the body is transform-neutral and harmless

**The assumption (stated).** Spec `reparent[].why`: "its parent is one of the removed door parts;
the nearest surviving ancestor is `sportsmuscle_body` (0)".

**Test 1 — is the re-parent a no-op on placement?** Parent frames and offsets in the donor and the
build (all four orphans keep `parent_space_offset = [0,0,0]`, and so do both doors):

```
bm-001  i=1 door_f_l        parent=0  pso=[0,0,0]
        i=16 door_f_l_window parent=1 pso=[0,0,0]   i=17 l_mirror parent=1 pso=[0,0,0]
        i=18 door_f_r_window parent=2 pso=[0,0,0]   i=19 r_mirror parent=2 pso=[0,0,0]
bm-002  i=16 … parent=0 pso=[0,0,0]   i=17 … parent=0   i=18 … parent=0   i=19 … parent=0
```

Since the door's own frame origin is the body origin, moving the child from door to body changes
nothing. **Test 2 — will they render?**

```
i= 16 sportsmuscle_door_f_l_window  beh=FrontLeftWindow   starts_deleted=0 disappears=1  model exists=True
i= 17 sportsmuscle_l_mirror         beh=None              starts_deleted=0 disappears=0  model exists=True
i= 18 sportsmuscle_door_f_r_window  beh=FrontRightWindow   starts_deleted=0 disappears=1  model exists=True
i= 19 sportsmuscle_r_mirror         beh=None              starts_deleted=0 disappears=0  model exists=True
```

**Verdict: HOLDS on the transform** (verified, not inferred — identity frames all round). **WEAK on
the consequence:** the card's premise is "the Batmobile has no doors" (PRT-1, R1), yet the car keeps
door **glass** and both **mirrors** as visible parts; nothing sets `starts_deleted`, and the windows
only vanish when broken. That is a lore gap (R1) inside a `done` card, and it is cheap to close
(set `starts_deleted` 1 or drop the two window parts) once someone decides whether the Batmobile
keeps side glass.

## B4-19 · Every part's model resolves

**The assumption (stated, Done criterion 2/3).** "models resolve 59/59 parts; 0 missing `.rbm`, 0 not
packed"; the MODLOG adds that the 98 new files were registered in `@files.xml` because "SmallPack
drops unregistered files".

**Test — presence (the card's own check) *and* the hash relation, which the check does not test:**

```
$ python (hash_jenkins(model path) vs the module's stored model hash)
model paths whose stored hash == hash_jenkins(path): 59 mismatch: 0
$ python (bm_parts.py --check step 3)
3. models resolve 59/59 parts; 0 missing .rbm, 0 not packed
```

**Verdict: HOLDS.** This is the strongest piece of the card: the path *and* the Jenkins hash of the
path agree for all 59, so the model reference cannot be half-right, and the `.toc` record's
offset/size is asserted against the `.ee`'s own SARC entry (tamper 1 catches a byte flip).

---

## What the card's readers should not conclude

1. That a green `bm_parts.py --check` means the module is *behaviourally* complete. It proves the
   table re-reads as written, not that the table points anywhere. The five carriers a JC3 part
   actually has — `constraint_index`, collision ids, `damage_type` in-table, `.lod` layout,
   `parent_space_offset` frame — are exactly the five places the card inherits a value rather than
   measures one, and four of the five are wrong against the fleet (B4-02…05, B4-14).
2. That "1 and 2 are free" is proven. It is an inference with zero precedent; the check cannot see
   the difference (B4-01).
3. That the build is inside R9. It reports **8,077.5 KB of 4,915** and says so; the green number
   belongs to a re-emit no card owns (B4-15).
4. That the turret will aim, the flaps will hinge, or the gatling will spin. The module declares
   three behaviour names and zero hinge pointers, and nothing in bm-002 supplies the `.physicsc`
   side (B4-02, B4-03).

## What the record should say (cheapest fixes, no guessing)

* Row provenance: `number_of_blades` → "type default (size 1 / default 1), corroborated 6/6";
  `rotation_axis` → "T-12 `axis_jc3`; **sign contradicts 6/6 shipped rows (+Z), frame UNKNOWN**".
* Collision source string: replace the 599/11,643 sentence with the class cut that decides it
  (0/319 weapon-class, 14/1,421 lamps) — then either give the new parts ids or record the exception
  on purpose.
* Damage types: either map `Boat_Generic`/`Train_Generic`/`Plane_Control_Surface` to in-table
  equivalents (`Land_Generic` behaves like the turret row) or record that 7 parts fall back to
  `Default` and what that costs (50/30/20 vs 200/0/50).
* Limits: add "the `.epe` keeps two `CInteractionGraphExit` names for the removed doors" next to the
  deform-module note.
* Done line: say which of the three checks reads `Builds/`; `jc3parts.py check` does not.
* `.lod`: the 8 lamp files need the `-`,`-` placeholders to match every shipped 3-LOD file, or a
  phase-Q probe that proves the short form parses.

## What would settle the open ones (all one-variable, phase Q or offline)

1. **Array order vs field** (B4-01): replay bm-002 with the 40 survivors renumbered 0…58 so
   `position == part_index`, in one probe; if the car looks identical, the field reading is harmless
   and the renumber build is the safer ship.
2. **Turret hinge** (B4-02/-03): copy the medium tank's two hinges (yaw −179…179 about +Y at the
   trunnion, pitch −5…20 about +X) plus the two unnamed point strings `id:80201E4D` /
   `id:5C19E7E0` into the `.physicsc`, set `constraint_index` 50/51/53, and compare with the current
   build — that is B-05's real content and `TURRET.md` says exactly what to copy.
3. **Collision** (B4-04): give the 19 parts ids like every shipped part of their class, then re-run
   `jc3hkx.py check --all --file … --against <donor>`; B-10's 5-hull set is unchanged.
4. **Spin sign** (B4-09): two builds, +Z and −Z, one probe each (R13).
5. **Lamp `.lod`** (B4-14): rebuild the 8 lamp `.lod` files with the shipped `-`,`-` form and diff
   the model set; no other change.

## How this was produced (read-only)

Every number above comes from a command run against the tree; the long ones were ad-hoc
`python -` heredocs (no file written), the tools were the repo's own:

```
python Tools/scripts/bm_parts.py --check
python Tools/scripts/jc3parts.py check
python - (jc3adf.Adf / walk over Builds/bm-002/…/*.vmodc, tmp/b05/base.xml, tmp/b04/*.vmodc)
python - (jc3adf over E:/Modding/JustCause3/_grab/tmp|probe/*_vehicle_parts.vmodc — 80 files, 47 rotating rows,
          85 aim rows, 148 hinged rows, 227 door rows, 31 turret/cannon/brake/gatling parts)
python - (rbmhdr.read_header over the 19 new + donor parts for AABB centres; hash_jenkins over 59 model paths)
python - (struct header diff base.vmodc vs rt.vmodc; printable-string census)
python - (E:/Modding/JustCause3/_grab/entities/*sportsmuscle_civilian_01.ee.json — VehicleDamage 24 types)
```

Read-only discipline: this file is the only write. No launch, no `D:/Games` write, no commit, and no
game data copied into the repo.
