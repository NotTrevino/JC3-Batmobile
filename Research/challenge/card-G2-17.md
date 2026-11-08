# Assumption challenge — backlog card G2-17 (`CForcePulse`)

Read-only pass over the finished card: `GRAB_BACKLOG.md` §0.5 (R1–R14), the G2-17 card (§6, line 663),
its §12 row (line 1300), the MODLOG `G2-17 · CForcePulse — intended change` and `— done` sections,
and the outputs `Research/JC3Grab/FORCEPULSE.md` + `FORCEPULSE.json` + the generator
`Tools/scripts/jc3forcepulse.py`, plus the population it reads (`E:/Modding/_JC3grab/detail/*.ee.json`,
the archive index, and `FEATURE_CENSUS.json`).

Constraints honoured: no game launched, nothing written into `D:/Games`, nothing committed, no
secrets, no `--write`. `--check` rebuilds in memory only and the `.json`/`.md` were not touched:

```
$ python Tools/scripts/jc3forcepulse.py --check
PASS: 307 pulses / 232 entities / 79 chassis, 31 members, 23 tunes, owners {'(none)': 14,
'CAirPlane': 18, 'CBoat': 35, 'CBulletWeaponBase': 29, 'CCar': 126, 'CHelicopter': 23,
'CMissileWeaponBase': 25, 'CMotorBike': 19, 'CRPGFireLeachWeapon': 6, 'CTrain': 12},
unowned 14, horn tunes 0, collision tunes 0                                   EXIT=0
```

The extra work this pass did was **decoding the vehicles the card did not decode** (82 `.ee`, all
read-only, in memory) — that is where every headline-level finding below comes from.

## VERDICT

**Four BROKEN, five WEAK, five HOLDS.** The artefact is well made where it is narrow: the 31-member
census reproduces, the 307 pulse oids are unique and each has at most one owner, the owner pointer
`id:B5AE7986` behaves exactly as described (1:1, null elsewhere, verified on three entities), and the
tunes are byte-identical copies across entities (`car_explosion_medium.ftunec` is
`sha1 c94b5a47128c`, 644 B, 8 identical numbers in the donor and in the medium tank).

What breaks is the word **fleet**. The generator walks `detail/*.ee.json`, and that directory holds
**232 of the 314 vehicle `.ee` in the index**. The missing 82 (81 DLC + one base-game build,
`v2602_helicopter_urga_lightassault_military_01_custom_mm230.ee`) carry **157 more pulses in 77
entities**, **8 tunes that are not in the 23**, and a new owner class `CUnmanedQuadcopterDrone`
(34 pulses). The true counts are **464 pulses / 314 `.ee` / 31 tunes / 33 unowned**, not
307 / 232 / 23 / 14. The limits paragraph does say "the census covers the 232 decoded vehicle graphs",
so this is disclosed — but the headline ("the fleet's blast component"), §2's table title ("The fleet"),
the HUD-facing number in the §12 row and the claim "every pulse is an explosion" all read as fleet-wide.

Two of the four breaks are arithmetic/logic, not scope: §4.2's `214 + 54 + 14` does not add up to 307
(54 is bullet+missile only, 29 + 25 + 6 is 60, and the 19 `CMotorBike` pulses belong to no group), and
the horn/collision refutation is a name-absence test that cannot possibly discriminate, because every
pulse in the sample is an explosion *by construction* — a horn-fired blast would still be named
`car_explosion_medium.ftune`.

| # | assumption | verdict |
|---|---|---|
| A1 | "the fleet" = the 232 decoded vehicle graphs | **WEAK** — 232 of 314; the missing 82 carry 157 pulses (disclosed in §6, contradicted by the headline) |
| A2 | every `CForcePulse` is an explosion / blast | **BROKEN** — DLC carries `mech_punch_force_pulse(.upgraded)`, `w501_sam`, `gen_explosion_3m`: a punch shockwave is the same class |
| A3 | `FEATURE_CENSUS.json` agreeing makes the counts independent | **WEAK** — same 232 and same decoder family; a genuinely different parser (`jc3detail`) does give 307/232 |
| A4 | `id:B5AE7986` is an *owner* pointer (member read by behaviour) | **HOLDS** — 1:1 owner→pulse, null elsewhere, no pulse has two owners |
| A5 | the pointer proves the carrier, not the trigger | **HOLDS** — and the record says so; `S_STUNT_USE_ITEM_VEHICLE` stays UNKNOWN |
| A6 | horn and collision are refuted by "no horn/collision in tune paths or pulse names" | **BROKEN** as a test (cannot discriminate); the conclusion survives by a different test |
| A7 | `214` root-owned + `54` weapon-owned + `14` unowned covers 307 | **BROKEN** — 29 + 25 + 6 = 60, and the 19 bike pulses are in neither group: 214 + 60 + 19 + 14 = 307 |
| A8 | every root-owned pulse uses "the explosion tune for that vehicle's own type" | **WEAK** — `CCar`-owned is 115 `car_explosion_medium` + 11 `fuel_tank_spherical_explosion_01` |
| A9 | each tune decodes to the same 8 numbers everywhere | **HOLDS** — 8 keys in all, `consistent` true for 23/23, byte-identical copies |
| A10 | `*RadiusMin` / `*RadiusPercentageMax` = "how much of the radius keeps full damage" | **WEAK** — name-based; DLC has Min 0.95 m with PercentageMax 1.0, which is not a pair of fractions |
| A11 | "everything sits at the entity origin except the EMP and barrel/cargo pulses" | **BROKEN** — 4 more off-origin pulses (2 yacht, 1 cargoplane, 1 mm340) |
| A12 | exactly one reference to a pulse besides the owner pointer | **HOLDS** for the scanned population (the mm340 `GraphScript`) |
| A13 | 14 unowned pulses, each explained by nesting | **WEAK** — the 82 undecoded `.ee` add 33 unowned, so "14" is sample-scoped |
| A14 | 307 distinct pulses, one owner at most | **HOLDS** — 307 oids, 307 unique, 0 pulses with two owners, 14 with none |

Counts: 5 HOLDS, 5 WEAK, 4 BROKEN.

---

## A1 — "the fleet" is the 232 decoded graphs. **WEAK**

```
$ python -c …   # index vs detail/
index .ee: 963            jc_vehicles .ee: 314            detail graphs: 232
decoded ⊆ index: True     vehicle .ee NOT decoded: 82
```

All 82 are `dlc/…` except one base-game file:

```
editor/entities/jc_vehicles/02_air/v2602_helicopter_urga_lightassault/
    v2602_helicopter_urga_lightassault_military_01_custom_mm230.ee
```

Decoding all 82 with the same reader the card uses (`jc3wiring.decode_epe`, in memory):

```
entities decoded: 82  with pulses: 77  pulses: 157  fails: 0
owners: {'CCar': 15, 'CMissileWeaponBase': 14, 'CHelicopter': 7, 'CBulletWeaponBase': 29,
         'CUnmanedQuadcopterDrone': 34, 'CAirPlane': 4, 'CBoat': 16, '(none)': 33,
         'CRPGFireLeachWeapon': 4, 'CMotorBike': 1}
tunes: 19 (11 already in the 23, 8 new)
```

and the base-game file the card misses, on its own:

```
== v2602_helicopter_urga_lightassault_military_01_custom_mm230.ee
   objects 369 pulses 2
    ForcePulse  w604_helicopter_mgun_impact.ftune   owner ['CBulletWeaponBase']
    CForcePulse helicopter_explosion_medium.ftune   owner ['CHelicopter']
```

So the real population is 314 `.ee` / 464 pulses / 31 tunes. The §6 limit is honest about the frame
("the census covers the 232 decoded vehicle graphs, not every `.ee` in the index"), which is why this
is **WEAK** rather than broken — but every other section, and the §12 row, present the numbers as the
fleet's. A card whose question is "find what triggers it by comparing vehicles that differ in
behaviour" is exactly the card that should not stop at 74 % of the vehicles, especially when the
missing 26 % is the DLC set where the unusual pulses live (mech, drones, SAM).

## A2 — every `CForcePulse` is an explosion. **BROKEN**

The md opens: "**Trigger: explosion, and the owner says which explosion.** Every one of the 307 pulses
… is a blast: its `SettingsFile` names one of 23 explosion tunes". Decode a DLC mech:

```
== v0805_car_na_mech_cannon.ee  pulses 5
   CForcePulse                …/jc_explosions/vehicles/car_explosion_medium.ftune
   MechPunchForcePulseAI      …/mech_punch_force_pulse.ftune
       PlayerDamage 550 / 22 m, AIDamage 100 / 22 m, RadiusMin 0.95, PercentageMax 1.0
   MechPunchForcePulse        …/mech_punch_force_pulse.ftune
   MechPunchForcePulseUpgrade1 …/mech_punch_force_pulse_upgraded.ftune
       PlayerDamage 1000 / 40 m, AIDamage 100 / 40 m
   w628_mechloader_cannon_explosion …/w628_mechloader_cannon_explosion.ftune
```

`MechPunchForcePulse` is a mech's *punch*, not an explosion, and it is the same class with the same 31
members. The eight tunes the sample never sees are:

```
gen_explosion_0.5m_nodamage, gen_explosion_3m, mech_punch_force_pulse,
mech_punch_force_pulse_upgraded, w143_fire_leach, w501_sam,
w628_mechloader_cannon_explosion, w630_mech_mgun_impact
```

The class is the engine's **radial force/damage pulse**; explosions are one use of it. The card's
title ("the fleet's blast component") and its central inference are therefore sample artefacts — this
is precisely the R5 shape: the component was described by the role it plays in the sampled vehicles,
and the name (`CForcePulse`, `ForcePulse`, `MechPunchForcePulse`) disagrees with the description.
For WPN-5 this matters: an EMP built as a `CForcePulse` is a radial damage/impulse emitter whose
*visual* is an explosion effect — nothing in the component says "explosion".

## A3 — the census agreement is independent confirmation. **WEAK**

"`FEATURE_CENSUS.json` agrees object for object" is repeated in §2 and asserted in the invariants. That
file was produced from the same 232 `detail/*.ee.json` population, so agreement proves the two scripts
read the same graphs, not that the graphs are the fleet (see A1).

What does corroborate the *count* is a different parser over the same 232:

```
detail-json CForcePulse objects: 307  entities: 232      # class field, not the pulse decoder
```

So `307 / 232` is right for the frame; `79 chassis` and `23 tunes` are right for the frame. The frame
is the problem, not the arithmetic.

## A4 — `id:B5AE7986` is an owner pointer. **HOLDS**

Tested by behaviour, not name — the field is read on every object and resolved against the graph's own
oids, on three entities picked for their different owner shapes:

```
== v0201_car_capstone_mediumtank_military_01.ee
   CBulletWeaponBase w603_mediumtank_mgun -> 00000000          (unresolved, null)
   CCar              v0201_…_military_01  -> 7AC7278D=FFFFD6C3 PULSE
   CBulletWeaponBase w602_mediumtank_canon-> 7EE245DC=FFFFB14B PULSE
== v1202_boat_capstone_corvette_military_01.ee
   CBulletWeaponBase w616_corvette_canon  -> 95F550ED=FFFF4AFC PULSE
   CBoat             v1202_…_military_01  -> BC8D6F91=FFFFCDFB PULSE
== …_signature_preorder.ee
   CCar              …_signature_preorder -> C5D1C8E5=FFFFDC4D PULSE
   CMissileWeaponBase w618_…_missile      -> F8894393=FFFF0D20 PULSE
```

Fleet-wide from the artefact: 307 oids, 307 unique, **0 pulses with more than one owner**, 14 with
none; the only non-null value is always a pulse oid, and the only other reference to a pulse in the
whole sample is one `CGraphScriptGameObject`. "Owner" is a fair reading of a 1:1 inbound pointer that
is null on every non-owner. What the field is *called* stays unknown, and the record says so.

## A5 — the pointer gives the carrier, not the trigger. **HOLDS (as a limit)**

The record states this twice ("the files prove the owner and the tune, not the moment"), and it is
true: nothing in the graph marks a condition (no "on death", "on impact", "on use" member among the 31
— the members are eight numbers, a tune path, a world transform, a material table reference and
pointers). So the EMP's "use item fires it" inference is correctly left as a Q-1 probe.

One consequence the record does not draw: since the field is shared by destruction blasts
(vehicle root) and weapon blasts (weapon component), the engine's use is at least two-ended, which is
further evidence the field is a generic "this component's force pulse" slot rather than a
destruction-specific one.

## A6 — horn and collision are refuted. **BROKEN as stated**

The refutation offered is:

> horn | 178 entities carry an `SAttachedEffect` named `horn`; **0 of 23 tune paths and 0 of 9 pulse
> names mention a horn** | horn does not trigger a pulse

That test cannot discriminate. Every pulse in the sample *is* an explosion tune (A2), so a pulse fired
by the horn would still be `car_explosion_medium.ftune`; and pulse names are class-derived
(`CForcePulse` ×263) or weapon-derived (`w618_sportsmuscle_missile` ×1), never trigger-derived. Under
the hypothesis "the horn fires the car's blast", the observation "no tune is named horn" is exactly
what you would still see. The same argument kills the collision row ("0 of 23 tune paths mention
collision").

The conclusion is nevertheless supportable, by a test the record already has the data for but does not
use: **no horn or collision object anywhere in the sample points at a pulse.** The at-rest horn object
is pure sound + scalars —

```
SAttachedEffect horn  55E069CE=FFFF79C9   parent SEffects
   Sound  FD,69,C6,3C,84,E6,FA,43,B0,67,7E,AE,99,A5,9C,E1
   Usage  -962520269      world 1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0.02282715,0,1
```

— and the fleet-wide reference scan in the artefact (`other_refs = 1`, the mm340 GraphScript) would
have caught a horn object holding a pulse oid. So: verdict on the *claim*: unsupported by the stated
test; the true refutation is weaker but real (no data pointer from a horn or a collision object), and
neither refutes an engine-side event mapping. The record should say the last part.

## A7 — `214 + 54 + 14` covers 307. **BROKEN (arithmetic)**

§4.2:

> **214 pulses are owned by the vehicle root class** (CAirPlane, CBoat, CCar, CHelicopter, CTrain)
> **54 pulses are owned by a weapon component** (CBulletWeaponBase, CMissileWeaponBase, CRPGFireLeachWeapon)

Counted from the artefact by owner class:

```
root-owned (CCar,CAirPlane,CBoat,CHelicopter,CTrain): 214
CBulletWeaponBase + CMissileWeaponBase:               54
all weapon-owned (incl. CRPGFireLeachWeapon 6):        60
CMotorBike:                                            19
(none):                                                14
214 + 60 + 19 + 14 = 307
```

Three defects in one sentence: 29 + 25 + 6 is **60**, not 54; the 6 RPG pulses are named in the
parenthesis but excluded from the number; and **19 `CMotorBike` pulses belong to neither group**
(a bike root is not in `ROOT_CLASSES`, so it is not "the vehicle root class" either — the bike entities
carry root class `(none)` in §2's table). The generator's own `render_md` computes
`weapon_pulses` as bullet+missile only and `root_pulses` from `ROOT_CLASSES`, so the two numbers were
computed correctly and then written into a sentence that makes them exhaustive.

## A8 — every root-owned pulse uses its own type's tune. **WEAK**

Cross-tabulated by owner (not by entity root class):

```
owner CCar          car_explosion_medium.ftune               115
owner CCar          fuel_tank_spherical_explosion_01.ftune    11
owner CCar  → 126 = the census's CCar 126
owner CBoat         boat_explosion_large 8 + boat_explosion_medium 27 = 35
owner CHelicopter   helicopter_explosion_medium              23
owner CAirPlane     airplane_explosion_medium                18
owner CTrain        train_explosion_medium                   12
owner CMotorBike    bike_explosion_medium                    19
```

So "every one of them uses the explosion tune for that vehicle's own type" holds for 203 of 214, and
the 11 exceptions are the fuel-tanker blasts (`fuel_tank_spherical_explosion_01`, 1000 damage / 50 m).
The record's own tune table shows those 11, so the data is there; the sentence glosses them. It also
never says the class→tune map is not 1:1 — `CCar` → two tunes — which is the fact a port needs.

## A9 — one tune, one set of eight numbers, everywhere. **HOLDS**

```
tune keys per tune: Counter({8: 23})     tunes with consistent=False: []
```

Independent spot-check of the most common tune in two different entities (donor car and medium tank),
reading the container member directly:

```
v0300_…_civilian_01.ee         members matching car_explosion_medium.ftunec: 1
   size 644  sha1 c94b5a47128c  {PlayerDamage 500, PlayerDamageRadius 5.0,
                                 PlayerDamageRadiusMin 0.0, PlayerDamageRadiusPercentageMax 0.0, …}
v0201_…_military_01.ee         members matching car_explosion_medium.ftunec: 1
   size 644  sha1 c94b5a47128c  (same eight values)
```

The members are literally the same bytes, so "the same tune decodes identically in every entity that
carries it" is exact, and the `tune_of` stem match is unambiguous in both (one member per entity).

## A10 — what `*RadiusMin` and `*RadiusPercentageMax` mean. **WEAK**

The record states:

> `*RadiusPercentageMax`/`*RadiusMin` say how much of the radius keeps full damage - 0.0/0.0 on the
> stock vehicle blasts (damage falls off at once), 1.0/1.0 on the EMP and the bomb.

This is read from member names (R5 territory) and the data argues against a single "fraction of
radius" reading: the DLC values are `RadiusMin 0.95` (a distance in metres, matching its siblings
`Radius 22.0`) with `PercentageMax 1.0`; `w604_helicopter_mgun_impact` — one of the 23 — has
`RadiusMin 0.9` / `PercentageMax 1.0` too. A pair that mixes a metre-scale inner radius with a
fraction is plausible (inner full-damage radius, then linear falloff to the outer radius), but nothing
in the files proves it, and "0.0/0.0 … damage falls off at once" is one reading among several (an
inner radius of 0 and a falloff starting at 0 could equally mean "no falloff"). Verdict **WEAK**:
unlabelled inference presented as decoded behaviour; the numbers are right, the semantics are not
established.

## A11 — "everything sits at the entity origin except …". **BROKEN**

```
positions: {'(-9.616, -2.3759, -4.2695)': 1, '(0.0, 0.0, 0.0)': 292,
            '(0.0, 0.2613, 5.5002)': 2, '(0.0, 2.0356, 0.6992)': 1,
            '(0.0, 4.8101, 0.0)': 1, '(0.0129, 0.5109, 0.0)': 10}
```

The md says: "Everything sits at the entity origin except the EMP pulse (over the flatbed device) and
the barrel/cargo pulses (on the cargo)." Listing every non-origin pulse:

```
10 × v0505_…_cargo_barrel            force                 (0.0129, 0.5109, 0)      [mentioned]
 1 × v0505_…_rebel_emp_01            EMP                   (0, 2.0356, 0.6992)       [mentioned]
 2 × v1300_boat_kensington_motoryacht CForcePulse          (0, 0.2613, 5.5002)      [NOT mentioned]
 1 × v4603_plane_urga_cargotransport_military  w602_mediumtank_canon (0, 4.8101, 0) [NOT mentioned]
 1 × v4603_plane_urga_cargotransport_mm340     explosion_force_pulse (-9.616, -2.376, -4.27) [NOT mentioned]
```

Four pulses are off-origin and unexplained by the sentence — including the mm340 one at −9.6 m, the
oddest value in the table. The numbers in the table are right; the prose summary of them is wrong.

## A12 — exactly one non-owner reference. **HOLDS (within its scope)**

The scan in `build()` looks for a pulse's oid in every string property of every other object of the
same graph, excluding `_object_id` and the owner pointer itself. It finds one:

```
v4603_plane_urga_cargotransport_mm340.ee  CGraphScriptGameObject  id:65424AC6 -> 875B9AD5=FFFF75FD
```

which is the `BOMB_JEEP` rule's pulse (`w704_m488`). I re-ran the equivalent scan logic on samples and
found no additional reference; the horn objects (A6) carry none. Scope limit worth stating: an object
in *another* entity could hold the oid, and no cross-entity sweep is possible or meaningful — the
record's "in the fleet" means "in the scanned graphs", which is fine but should be worded that way.

## A13 — 14 unowned pulses. **WEAK**

For the 232-graph frame the list and its explanations check out:

```
10 × cargo_barrel      barrel_explosion.ftune        parent CRigidObject:barrel
 2 × cargo_random      gen_explosion_5m_nodamage      parent CRigidObject:air_conditioner…
 1 × rebel_emp_01      truck_emp.ftune                parent CCar:…_rebel_emp_01
 1 × …_mm340           w704_m488.ftune               parent CVehicleRule:BOMB_JEEP
```

But the 82 undecoded `.ee` add **33 more unowned pulses**, and the new owner class
`CUnmanedQuadcopterDrone` (34) is not in the census at all. "14 unowned" is a frame number presented as
a fleet fact; the EMP being "the only unowned vehicle blast" is true only inside the frame. Verdict
**WEAK**, same root cause as A1.

## A14 — 307 pulses, distinct, at most one owner. **HOLDS**

```
oids: 307   unique: 307
pulses with >1 owner: 0        pulses with 0 owners: 14
sum(owners) = 307              unowned list length 14 = owners['(none)']
world present on 307/307       named members exactly the five declared
```

These are the invariants the resumed session repaired, and they now match the data. The repair story in
the MODLOG (invariants rewritten to the measured facts after an independent `ElementTree` recount) is
the right process; the flaw this challenge finds is not in the counts but in what the counts were
taken to be the population of.

---

## What would close the gap cheaply

1. **Decode the 82 and widen the frame** (or retitle the card). Same reader, ~2 minutes, and the
   numbers become 464 / 314 / 31 with the mech and drone owners included. If the frame stays 232, the
   md should say "the 232 decoded vehicle graphs" in the headline, not "the fleet".
2. **Fix §4.2's sentence**: 214 root-owned + 60 weapon-owned + 19 bike + 14 unowned = 307, and say the
   class→tune map is not 1:1 (`CCar` = 115 car + 11 fuel-tank blasts).
3. **Replace the horn/collision argument** with the one the data supports: no horn or collision object
   holds a pulse oid anywhere in the sample; the trigger remains UNKNOWN.
4. **Relabel `*RadiusMin`/`*RadiusPercentageMax` as inferred**, or mark them UNKNOWN like the rest of
   the trigger question, and add the four missing off-origin pulses to the positions sentence.
