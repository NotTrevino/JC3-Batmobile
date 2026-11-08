# Assumption challenge — G2-11 · Weapon wiring per armed vehicle

**Scope.** Finished card `GRAB_BACKLOG.md:598-611` (M, deps G2-10), its §12 row (`:1294`), MODLOG
§"G2-11 · Weapon wiring per armed vehicle — done" (`:9332`) and the outputs it names:
`Research/JC3Grab/WEAPON_WIRING.md` (2,045 lines), `WEAPON_WIRING.jsonl` (53 rows),
`Tools/scripts/jc3wiring.py`. Rules read first: `GRAB_BACKLOG.md` §0.5 R1–R14.

**Method.** Re-ran the card's check, then attacked each claim with the data on disk: the 53 cached
`.epe` graphs (`E:\Modding\JustCause3\_grab\wiring\epe\*.xml`), `FEATURE_CENSUS.json`,
`INDEX.jsonl`, and — read-only — the shipped `.arc` files at `D:\Games\Just Cause 3` (the
generator itself reads them; nothing was written there, no game launched, nothing committed).

**Change record (AGENTS.md).** Only file written: this one,
`Research/challenge/card-G2-11.md` — the path the task names, alongside the existing
`Research/challenge/card-G1-*.md`. Revert: delete it.

**The card's own check, re-run:**

```
$ python Tools/scripts/jc3wiring.py --check
[1/53] v0200_car_capstone_apc_debug.ee: 1 weapons, 0 driver, 1 gunner
…
[53/53] v5603_train_urga_monorailmissilecar_military_01.ee: 1 weapons, 0 driver, 0 gunner
PASS: 53 entities, 88 weapons, 81 bound, 7 unbound, 193 seats, md 2045 lines
EXIT=0
```

The machine is intact. Everything below is about what the 53 and its numbers are taken to mean.

---

## VERDICT

| # | assumption | verdict |
|---|---|---|
| G1 | "53/53 armed entities" is the armed fleet | **BROKEN** |
| G2 | the totals (88 / 62 / 19 / 81+7 / 193 / 54 / 23) | **HOLDS** for the 53 |
| G3 | four slot pointers per root, max 2 driver, no third slot | **HOLDS** |
| G4 | the seat↔weapon link is structural, "a geometric join, not a pointer" | **BROKEN** |
| G5 | the 1.05 m join, in metres | **HOLDS** (recomputed) |
| G6 | "no button mapping"; `action_1`/`action_2` are 1/2 on armed and unarmed alike | **WEAK** |
| G7 | no switching carrier "anywhere in the `.epe`" | **HOLDS** for the 53, **WEAK** for the fleet |
| G8 | `CLightWeaponComponent` is a light, "30 components on 9 entities" | light **HOLDS**, count **BROKEN** |
| G9 | "22 of 88" carry `MountAttach`; "the other 59 driver weapons" have none | **HOLDS** (typed, not derived) |
| G10 | six property names recovered by Jenkins hash match | **HOLDS** (all six recomputed) |
| G11 | the `.md` is generated and `--check` diffs it | **BROKEN** — the shipped file contains `{len(rows)}` |
| G12 | the 7 unbound components are inert variants | **HOLDS** (nothing references them) |
| G13 | the cargo-plane variant carries a second root (54 roots) | **HOLDS** |
| G14 | "driver" / "gunner" labels | **WEAK** (inference, but corroborated) |
| G15 | the two unarmed samples carry null slots and `action_1/2` = 1/2 | **HOLDS** |

**One-line summary.** The decode is good work: every count in the doc recomputes exactly, the
six hash-recovered names are real, and the geometric join reproduces to the millimetre. But the
"fleet" is 232 decoded base-game graphs, and 42 more vehicle `.epe`s in the same index carry
weapon classes — including one base-game variant that is not in the 53 — so every fleet-worded
answer is a sample answer; and the card's central negative ("driver vs gunner is structural …
not a pointer") is contradicted by 19 `CInteractionGraphPointNode → weapon` pointers it did not
see.

---

## G1 · "53/53 armed entities" — is that the fleet?

**Doc / tracker.** §3 "armed entities **53**"; §2(c) "No. The most bound weapons on one entity is
2"; §2(d) "every other land vehicle is gunner-only or unarmed"; tracker "53/53 armed entities".

**Assumption (silent).** The 53 are all the armed vehicles, so the totals are the fleet's.

**Test 1 — what the 53 are built from.** `FEATURE_CENSUS.json`:

```
inputs: {'detail_graphs': 232, …}
totals: {'entities': 232, 'armed_entities': 53, 'armed_chassis': 21, …}
```

`jc3_feature_census.py`'s docstring: input is `detail/*.ee.json` "every vehicle `.epe` graph as
rows (**232 files**)". The index holds **314** vehicle `.ee`, 81 of them under `dlc/`:

```
vehicle .ee in index: 314
  editor/entities/jc_vehicles/01_land 156, 02_air 42, 03_sea 35
  dlc/mech_land_assault/editor/entities 44, dlc/bavarium_sea_heist/editor/entities 21,
  dlc/sky_fortress/editor/entities 14, dlc/v0805_sportmech/editor/entities 2
census armed path prefixes: {'02_air': 23, '01_land': 18, '03_sea': 12}   ← all base-game
```

So the 53 = armed among the 232 decoded **base-game** graphs. `wc -l` on the graph dir gives 232,
and `glob` finds no graph for any DLC entity.

**Test 2 — is anything outside the 53 armed?** The weapon class names live in each `.epe`'s name
table, so a raw byte scan answers without conversion. Control first:

```
v0201_…_mediumtank_military_01.ee   94368B  SWeaponPoint=1 Bullet=1 Missile=0   (armed)
v0200_…_apc_military_01.ee         100294B  SWeaponPoint=1 Bullet=1 Missile=0   (armed)
v0300_…_sportsmuscle_civilian_01.ee 109526B SWeaponPoint=0 Bullet=0 Missile=0   (unarmed)
```

All 314 vehicle `.ee`, no errors:

```
probed: 314 errors: 0
entities whose .epe names a weapon class: 95
  in census armed set: 53
  NOT in census: 42
dlc probed: 81   dlc armed by this test: 41
base probed: 233 base armed by this test: 54
base armed entities missing from the census:
  ['editor/entities/jc_vehicles/02_air/v2602_helicopter_urga_lightassault/'
   'v2602_helicopter_urga_lightassault_military_01_custom_mm230.ee']
```

**Test 3 — the 42 are really armed** (weapon instance names, not just class names):

```
v2602_…_military_01_custom_mm230.ee   86220B
   weapons=['w604_helicopter_mgun','w604_helicopter_mgun_impact']
   classes=['BarrelSpinWeaponComponent','CBulletWeaponBase','PPCBarrelSpinWeaponComponent','PSWeaponPoint']
   graph on disk: []            ← no detail graph, hence not in the census
v1706_boat_na_rocketboat_01.ee        62977B
   weapons=['w501_sam','w503_missile_capstone_billfire','w630_rocketboat_mgun', …]
   classes=['CBulletWeaponBase','CRPGFireLeachWeapon','SWeaponPoint','WeaponFirePoint','WeaponPos']
v0806_car_na_sportmech_01.ee         105936B
   weapons=['w629_mech_magnet','w143_fire_leach','w503_missile_capstone_billfire', …]
   classes=['CBulletWeaponBase','CRPGFireLeachWeapon','MagnetWeaponComponent', …]
```

The base-game `custom_mm230` variant is the decisive one: same chassis as three entities that
*are* in the 53, same weapon (`w604`), same component set — and it is absent because its detail
graph was never produced (232 of 233 base vehicle `.ee`), not because a rule excluded it.
`jc3detail.py` contains no `skip`/`exclude`/`custom` filter.

**Verdict: BROKEN.** "53/53" means "53 of the 53 the census saw". Against the index the armed
count is **at least 54 base-game + 41 DLC = 95 vehicle entities**, and the DLC set contains
weapons the card never lists (`w630_rocketboat_mgun`, `w629_mech_magnet`). The card's In-list
inherits 53 honestly, but the doc's fleet-worded answers and the tracker row do not say "of the
232 decoded base-game graphs", and 42 armed entities sit outside. (Method limit: the scan reads
class names from the name table; it does not decode the DLC property graph, so I can prove they
*carry* weapon components, not how many slots they bind.)

---

## G2 · the totals, recomputed from the jsonl

```
rows: 53
weapon components: 88
by class: {'CBulletWeaponBase': 57, 'CMissileWeaponBase': 25, 'CRPGFireLeachWeapon': 6}
bindings: main_weapon 37, secondary 23, mounted_weapon 14, mounted_weapon_2 5, CCar::main 1, CCar::secondary 1
unbound: 7
driver/gunner per row: {(2,0):24, (1,0):14, (0,1):9, (0,2):5, (0,0):1}   → 62 driver, 19 gunner
roots: 54 over 53 rows (one row has 2)
seats: 193
distinct weapon names: 23
weapon points: 300; moving-part rows: 112 (36 entities)
weapon_type: {'2': 88}
```

Every figure in the doc, the tracker row and the MODLOG matches. The census cross-check agrees on
the class totals (`CBulletWeaponBase objects=57`, `CMissileWeaponBase 25`, `CRPGFireLeachWeapon 6`).

**Verdict: HOLDS** (arithmetic and cross-source agreement; the *scope* is G1's problem).

---

## G3 · "four slot pointers per root … no file has a third driver slot"

**Test.** Rather than trust the four property keys, I swept **every property of every object** in
all 53 graphs for a value equal to a weapon component's `_object_id`:

```
properties whose value is a weapon component: {'root slot property': 81, 'OTHER': 107}
  of the OTHER: 88 are the component's own `_object_id` (self), 19 are CInteractionGraphPointNode ids (see G4)
```

81 weapon-valued properties are exactly the four slot keys on a root — nothing else on a root, on
a component, or on a part points at a weapon. `mounted_weapon` is present (null) on all 54 roots,
and the two trailing pointers are null on all 53 (the check verifies that too).

**Verdict: HOLDS** for the 53. The "no third slot" claim is a statement about these pointers, and
it is right: the root's only weapon channels are the four properties.

---

## G4 · "Driver vs gunner is structural, not per-weapon … the nearest-gunner-seat line is a geometric join, not a pointer"

**Doc** (§6, first bullet). "No weapon component points at a seat. The distinction is the slot
set … The nearest-gunner-seat line is a geometric join between the weapon's world translation and
the seat point, **not a pointer**."

**Test.** The property sweep above found 19 non-slot weapon pointers, all on
`CInteractionGraphPointNode`, all under the `CInteractionGraph` of the root:

```
('CInteractionGraphPointNode', 'id:1E0D3888', 'point.mounted_weapon')  9
('CInteractionGraphPointNode', 'id:1E0D3888', 'point.gunner.right')    5
('CInteractionGraphPointNode', 'id:1E0D3888', 'point.gunner.left')     5
```

A concrete one (APC):

```
node: /root/3/CInteractionGraph/5
   chain: point.mounted_weapon(CInteractionGraphPointNode) <- graph(CInteractionGraph)
          <- context(CInteractionContext) <- -
   id:1E0D3888 = 02DB2482=FFFF5911   name = point.mounted_weapon
```

`02DB2482=FFFF5911` is the `_object_id` of the APC's `w206_mounted_capstone_m2hm`. The node is a
**seat point** — a sibling of `point.driver`, `point.passenger1`, `point.gunner.stunt` in the same
interaction graph — and the property is null on every other point. So the entity states, per
seat point, which weapon belongs there, for exactly the 19 gunner weapons. The doc's sentence "no
weapon component points at a seat" is literally true (the arrow runs seat→weapon), but the
conclusion it supports — that the association is structural only and had to be recovered
geometrically — is false, and the 19 nearest-seat distances are a workaround for a pointer the
script did not read.

**Verdict: BROKEN.** This is the R5 pattern in reverse: the card trusted the names of the four
slot properties and missed the member that actually carries the behaviour.

---

## G5 · the 1.05 m join and its unit

**Test.** Recomputed from the raw world matrices of the heavy patrol boat, using the script's own
`xyz()`/`dist()`:

```
weapon at [2.6162, 2.511, -0.2434]
   dist to point.driver       = 3.8900 m
   dist to point.gunner.right = 1.0520 m
   dist to point.gunner.left  = 4.6080 m
weapon at [-2.62, 2.51, -0.24]
   dist to point.gunner.right = 4.6110 m
   dist to point.gunner.left  = 1.0540 m
```

The doc's 1.052 / 1.054 reproduce exactly, and the "slot order is not the seat order" reading
(mounted_weapon → right/seat 7, mounted_weapon_2 → left/seat 6) follows. Units are metres from
the row-major mat4 translation (fields 12–14); the game's vehicle space is metric, and the
magnitudes are consistent with a 2.6 m half-width hull.

**Verdict: HOLDS** (the only "units/coordinate" convention in this card, and it is reproducible).

---

## G6 · "no button mapping" — `action_1` / `action_2`

**Doc** §2(b): "Which button each maps to is not encoded in the entity — `action_1`/`action_2` are
`1`/`2` on armed and unarmed cars alike — and neither is switching".

**Test 1.** Values of the two members over all 54 roots:

```
root 'action*' properties: {'action_1': 54, 'action_2': 54}
   action_1 values: ['1', '4']
   action_2 values: ['2']
```

**Test 2.** Which root has 4:

```
v4603_plane_urga_cargotransport_military_cargo_tank.ee  CAirPlane  act1=4 act2=2  drv=2 gnr=0
v4603_plane_urga_cargotransport_military_cargo_tank.ee  CCar       act1=1 act2=2  drv=2 gnr=0
(all other 52 roots: act1=1)
```

So the flat statement is wrong: one of the 54 roots is `4/2`, and it is the one root that has no
driver weapon of its own (the transport plane; the two slots belong to the tank in its hold).
The *useful* observation survives — `action_1` is 1 on every armed root whether it has one weapon
or two, so it does not select a slot — but the doc's wording is inaccurate, and the test it
describes cannot exclude "action_1 = fire primary, action_2 = fire secondary" (a class-level
default would look identical on the unarmed civilian).

**Verdict: WEAK.** The conclusion ("no button mapping in the entity") is still the best reading,
but the stated evidence contains a wrong value and does not rule out the one candidate it names.

---

## G7 · "no active-slot index, no next/previous weapon action and no weapon group anywhere in the `.epe`"

**Test.** Searched the `.epe` bytes of all 53 armed entities for 17 candidate member names:

```
weapon_slot, active_weapon, next_weapon, prev_weapon, weapon_group, weapon_index,
switch_weapon, cycle_weapon, primary_weapon, secondary_weapon, weapon_select,
weapon_switch, weapon_list, weapons_array, weapon_array, current_weapon, mounted_weapon_3
→ candidate switch/slot names found across the 53 .epe files: NONE
```

The only weapon-named members in the tables are mounts and parts (`mounted_weapon`,
`weapon_anchor`, `weapon_break`, `*_weapon_mount_*`, `assault_weaponry_*`), and no object in any
of the 53 graphs carries a `weapons` property (checked every parsed object: zero hits).

**Verdict: HOLDS** for the 53. **WEAK** as a fleet statement: it was not run on the 42 armed
entities of G1 (the rocketboat and the mechs carry extra component classes —
`MagnetWeaponComponent`, `WeaponFirePoint` — that could bring their own members).

---

## G8 · "`CLightWeaponComponent` is a light … (30 components on 9 entities)"

**Test 1 — is it a light?** Dumped one (medium tank `warning_light`):

```
_object_id 1A4F0617=FFFF5F5A   Color 1,1,1,1   FalloffStart 1   Height 5   Radius 0.5
SpotLight 1   Priority 5   ProjectedTextureIndex 12   + 20 hashed members (Colour/…)
```

No muzzle, no fire point, no weapon tuning. The class is a light, on behaviour and not only on its
name.

**Test 2 — the count.** The census, same run, same 232 graphs:

```
CLightWeaponComponent   objects=30   entities=27   chassis=9
```

The doc says "30 components on **9 entities**" — 9 is the **chassis** count, not the entity count.
And the number is **typed** into the renderer (`jc3wiring.py:565`: `"… (30 components on 9
entities); …"`), so `--check`'s md diff can never catch it. That is R11 ("counts are generated,
never typed") broken in the generator's own prose.

**Verdict: the light classification HOLDS; the count is BROKEN** (should be 30 components over 27
entities / 9 chassis, and should be an f-string).

---

## G9 · "22 of 88 weapons carry a type-4 `MountAttach` … the other 59 driver weapons"

**Test.**

```
components with a type-4 point: 22
  gunner-bound: 19
  driver-bound: w616_corvette_canon ×3 (the three corvette variants)
bindings total: 81 bound → 81 − 22 = 59 bound weapons without a part
```

22/88, "all 19 gunner weapons (two parts each)" and "the corvette's driver cannon" all check out;
59 = 81 − 22 is the bound remainder, so "the other 59 driver weapons have no part pointer" is
arithmetically right (the three corvette rows are the driver weapons that do have one). The mount
strings also verify: 19 × `LeftHandMountedAttach`, 19 × `RightHandMountedAttach`, 13 ×
`MountAttach`.

But these four numbers are also **typed** (`jc3wiring.py:741-743`), not computed, and the doc's
"22 of 88" mixes components with entity rows (the corvette is one component name over three
entities). Same R11 exposure as G8, with the numbers currently correct.

**Verdict: HOLDS** (values), **WEAK** (provenance).

---

## G10 · the six Jenkins-recovered property names

**Test.** Recomputed every hash with the project's own `rbmhdr.hash_jenkins`:

```
main_weapon          851CAABE   ✓ (doc: id:851CAABE)
mounted_weapon_2     AC0BC788   ✓ (doc: id:AC0BC788)
tuning_file          AA7096C9   ✓
autoaim_tuning_file  6D4C8277   ✓
impact_usage         D075017A   ✓
weapon_category      19068026   ✓
```

Six of six, exact. I also tested 16 further candidates for the unnamed second driver slot
(`secondary_weapon`, `weapon_2`, `weapon_slot`, `active_weapon`, `next_weapon`, `weapon_group`,
`primary_weapon`, …) and none lands on `00568A74` — consistent with the doc's "no name found",
though 16 probes cannot prove absence.

**Verdict: HOLDS.** These are decoded names, not guesses. (Collision risk for a 32-bit match is
~1.1e6/2^32 ≈ 2.6e-4 per candidate set, so a spurious match is unlikely but not impossible.)

---

## G11 · "the `.md` is generated … `--check` regenerates this file and diffs it"

**Test.** The shipped doc contains an unrendered placeholder:

```
$ grep -n "{len(" Research/JC3Grab/WEAPON_WIRING.md
93:Counts above are components and roots, not vehicles. The cargo-tank variant carries a full
   `CCar` (tank) next to its `CAirPlane`, so the {len(rows)} entities hold 54 root objects; …
```

Cause, `jc3wiring.py:559-562`: the sentence is three concatenated literals, and only the first and
third carry the `f` prefix —

```python
a(f"Counts above are components and roots, not vehicles. The cargo-tank variant carries a "
  "full `CCar` (tank) next to its `CAirPlane`, so the {len(rows)} entities hold "
  f"{sum(len(r['root_classes']) for r in rows)} root objects; …")
```

The middle segment is a plain string, so `{len(rows)}` is emitted verbatim. `--check` re-renders
the same broken text and diffs it, so it PASSes on its own bug:

```
PASS: 53 entities, 88 weapons, 81 bound, 7 unbound, 193 seats, md 2045 lines
```

**Verdict: BROKEN** as validation. The generation is reproducible (that part is sound) but the
diff cannot detect a renderer defect, and the shipped artifact has one in the fleet-summary
paragraph. The "54 root objects" half of the same sentence is correct (54 roots over 53 rows).

---

## G12 · "Seven entity files carry an unbound component … inert duplicates"

**Test.** For the three unbound names (`w608_fighterjet_missile`,
`w612_fighterbomber_missile_air_lockon`, `w614_monorailmissilecar_missile`), searched every
property of every object in the graphs for a reference to them:

```
(no output — nothing points at them)
```

Not even a mount part or an interaction point references them, which is stronger than the doc's
"no slot references either". The monorail's only weapon sits under a `CTurretWeaponComponent` and
the entity has one seat (`stunt`), consistent with "AI/script turret".

**Verdict: HOLDS** for "inert" (nothing references them). "Variants left in the graph" remains an
inference about intent, but it is the only reading the data offers.

---

## G13 · the cargo-plane double root

**Test.** `roots per row: {1: 52, 2: 1}`, `sum roots: 54`; the one double row is
`v4603_plane_urga_cargotransport_military_cargo_tank.ee`, whose `CAirPlane` and `CCar` roots both
parse, and whose bindings are labelled `CCar::main_weapon` / `CCar::secondary (id:00568A74)`. The
tank root carries its own interaction context and slot values; the plane root's are null.

**Verdict: HOLDS** (and it is the reason the "54 root objects" sentence exists).

---

## G14 · the words "driver" and "gunner"

**Assumption.** The first two slots are fired by the driver, the last two by a gunner.

**Test.** There is no pointer from a slot to a seat, so the label is inference; what the data
shows is a clean partition:

```
(2,0) 24 rows   (1,0) 14 rows   (0,1) 9 rows   (0,2) 5 rows   (0,0) 1 row
```

No entity mixes the two pointer sets, every gunner-set weapon lands on a `MOUNTED_WEAPON`-state
seat, every gunner weapon carries the two-part `MountAttach` turret chain, and every driver-set
entity has a driver seat and no mounted-weapon seat. The word "driver" itself comes from
`main_weapon`'s recovered name.

**Verdict: WEAK** — an inference by elimination, well corroborated (and §6 says so explicitly,
which is to its credit), but it is not a decoded binding. G4 shows the game does encode the
seat↔weapon link, just not in the direction the card looked.

---

## G15 · the two unarmed samples

**Test.**

```
v0300_car_kensington_sportsmuscle_civilian_01  CCar  slots={'mounted_weapon':'00000000',
   'id:851CAABE':'00000000','id:00568A74':'00000000','id:AC0BC788':'00000000'}  action_1=1 action_2=2
v0604_car_urga_buggy_debug                    CCar  slots={all '00000000'}       (not in the armed set)
```

The four pointers are null and the action values match the armed cars, as the doc says.

**Verdict: HOLDS.**

---

## What I could not test

- **The 42 armed entities' wiring.** Proving they are armed needed only the name table; decoding
  their property graph needs `ConvertProperty`, which writes files — outside this task's
  read-only budget. So I can say the 53 is not the fleet; I cannot say what the missing 42 would
  add to the totals (the rocketboat alone would add `w630_rocketboat_mgun` and a
  `CRPGFireLeachWeapon`, both new to the 23-name list).
- **Whether `id:1E0D3888` has a name.** 16 Jenkins candidates failed; it stays an id of record
  (this is the same limitation the card records for `00568A74`).
- **Whether `action_1`/`action_2` are input actions.** No exe/binary read; the doc's own caveat
  ("the entity does not say which input") stands.
- **DLC/`custom` entities were not checked against `PARTS_TABLE.jsonl`**, so the "turret →
  cannon chain" argument was not re-run for them.

## Suggested corrections (for the card's owner, not applied here)

1. Scope §2/§3 explicitly: "of the 232 decoded base-game graphs (53 armed)"; or extend
   `jc3detail` to the 81 DLC + the missing `custom_mm230` base entity and re-derive the totals.
2. Add the 19 `CInteractionGraphPointNode → weapon` links to the slot model and replace the
   "geometric join, not a pointer" sentence in §6; the nearest-seat distances become a
   corroboration, not the evidence.
3. Fix `jc3wiring.py:565` ("30 components on 27 entities / 9 chassis") and make it an f-string;
   do the same for the typed "22 of 88 / 19 / 59" at `:741-743`.
4. Fix the missing `f` at `:560` and re-render; add a check that the rendered md contains no
   `{`-placeholder (the diff alone cannot see it).
5. Correct `action_1` "1/2 on armed and unarmed alike" to "1 on 53 of 54 roots; 4 on the cargo
   plane's own root, which carries no driver weapon".
