# Assumption challenge — G1-08 · Weapons: every value of every weapon/gadget archetype

Challenger: Freebuff (did not write this card). Date: 2026-10-29. Read-only: nothing under
`GRAB_BACKLOG.md`, `MODLOG.md`, `Tools/`, `Working/`, the rest of `Research/` or the game install
was written; no game launched. This report is the only file written.

Inputs read: `GRAB_BACKLOG.md` §0.5 (R1–R14), the G1-08 card (§7, line 390), the §12 row
(line 1276), `MODLOG.md` §"G1-08 · Weapons extraction — intent" (7797) and
§"G1-08 · Weapons record written" (7820), the outputs `Research/BatmobileGrab/WEAPONS.json`,
`WEAPONS.md`, and the script `Tools/scripts/grab_weapons.py`.

## VERDICT

**Sound in substance, with two broken side-claims and four weak/documented edges.** The numbers
behind the record reproduce: 62 objects / 13 classes (18 per package in Batmobile, MK2, Funhouse;
8 in Joker), 1,028 tags → 1,185 field rows, 1,002 named / 26 offset-only, 594 references =
466 resolved + 128 `missing-object` over 34 targets, 332 union fields × instances = 1,065
comparisons with 0 differences, 10 projectile names over 26 instances with 9 launcher targets and
1 without one in these packages. The card's `--check` gate is green.

What does not survive: the done section's "**the Joker package shares three objects
(`Batmobile_Cannon_V2`, `Batmobile_Booster`, `Batmobile_EMP_Burst`)**" — `Batmobile_EMP_Burst`
exists only in Batmobile/MK2/Funhouse, so the Joker shares **two**; and the "**`CHAIN.json` 8,595
bindings**" figure — `CHAIN.json` itself now reports `named_bindings: 9225`, `objects_bound: 105`.
Neither defect reaches the artefact (both are prose in the MODLOG, and the artefact's
`joker_only_objects: 5` / variant map are correct), so this is not a rework of the record.

Soft edges, all disclosed somewhere but worth naming: the unit line ("cm / cm/s / 16-bit angles",
an imported UE3 convention rather than something decoded here), `"missing-object"` meaning
*absent from the grab* rather than absent from the game, three null `ObjectNCRProperty` refs
silently outside the 594, the one class-default export counted among the "62 objects", and the two
card-named quantities (lifetime, inaccuracy-vs-heat) that resolve to 0 fields.

```
$ python Tools/scripts/grab_weapons.py --check
ok E:\Modding\JC3-Batmobile\Research\BatmobileGrab\WEAPONS.json
ok E:\Modding\JC3-Batmobile\Research\BatmobileGrab\WEAPONS.md
PASS: 62 objects, 13 classes, 594 references (128 missing-object), 0 variant differences, 10 projectiles (9 launcher targets, 1 unfired), 30 FX rows, 12 AkEvent rows
EXIT=0
```

The Done criterion in the card — "`--check` re-derives the file; the `.md` has one section per
class (11 gadget classes + projectiles); every reference resolves or is listed as
`missing-object`; 0 hand-typed values" — is met: 13 class sections exist (`## 6.` … `## 18.`,
11 `- gadget` + 2 `- projectile`), 466 + 128 = 594, and `--check` compares both files byte for
byte against a fresh derivation.

---

## A1 — "Every object whose class starts with `RBatmobile` or is `RBasicProjectile`" is the whole weapon universe

**Test.** Enumerate every class in the four vehicle packages and list what the selection misses.

```
records in 4 pkgs: 19996 | class None: 7
selected: 62 classes: 13
excluded records: 19934 distinct classes: 170
excluded with weapon-ish class: 1
    Playable_BatmobileJoker_SF RJokerMissileTarget Default__RJokerMissileTarget
```

The single near-miss (`RJokerMissileTarget`) was then opened:

```
TARGET OBJ: Playable_BatmobileJoker_SF RJokerMissileTarget Default__RJokerMissileTarget tags 0 []
```

**Verdict: HOLDS.** No excluded class is a weapon/gadget/projectile; the only weapon-flavoured
excluded name is a class default with zero tags (nothing to record). The 11 gadget classes the
record names (AllegianceSwitcher, Booster, Cannon, EMP, EMPMissile, HeavyCannon, MissileLauncher,
MissileLauncherJoker, Sonar, VehicleTracker, Winch) are all in the selection.

## A2 — The four packages are the fleet; the `_Std_*` packages hold no vehicle

**Test.** Class census of every `_Std_*` package in the grab.

```
Playable_Batmobile_Std_6_SF 92 classes: ['Material','MaterialExpressionScalarParameter','MaterialExpressionStaticSwitchParameter','MaterialExpressionTextureSampleParameter2D','MaterialExpressionVectorParameter','MaterialFunction','MaterialInstanceConstant','ObjectReferencer'] | RBatmobile*: []
Playable_BatmobileMK2_Std_SF 4 classes: ['ObjectReferencer','Package','RAddContentBatmobileMesh'] | RBatmobile*: []
Playable_BatmobileFunhouse_Std_SF 4 ... | RBatmobile*: []
Playable_BatmobileJoker_Std_SF 4 ... | RBatmobile*: []
```

**Verdict: HOLDS.** Materials, packages and `RAddContentBatmobileMesh` add-content stubs only.
`RAddContentBatmobileMesh` is the one thing in a `_Std_*` package that could have been mistaken for
a vehicle object; it carries no `RBatmobile*` class and no weapon fields.

## A3 — The "11 gadget + 2 projectile" split is behaviour, not class-name guesswork (R5)

**Test.** The split rests on a hard-coded `PROJECTILE_CLASSES` set containing `RBasicProjectile`
and `RBatmobileMissile`. Check what the 13 `RBatmobileMissile` objects actually carry.

```
Playable_BatmobileFunhouse_SF | Batmobile_EMPMissile_Projectile | proj: RBatmobileMissile.ExplosionTemplate -> Rocket.Batmobil_Rocket_Explosion | resolved
  ... RBatmobileMissile.Trail -> Batmobile_EMPMissile_Projectile.RocketTrail | resolved
  ... Projectile.MyDamageType -> Core.RDmgType_BatmobileCannon | missing-object
  ... RBasicProjectile.ProjectileMesh / ProjectileTrail / Projectile.CylinderComponent -> resolved
```

**Verdict: HOLDS.** Each `RBatmobileMissile` exports `Projectile.*` / `RBasicProjectile.*` fields,
an `ExplosionTemplate`, a trail and a collision cylinder — projectile behaviour, not just a
projectile-sounding name. The one class whose classification is declaration-by-set
(`RBasicProjectile`, 13 objects) is the base class the others name in their own field paths.

## A4 — 1,028 tags → 1,185 field rows; 1,002 named, 26 offset-only

**Test.** Recomputed from `WEAPONS.json`:

```
objects: 62
sum tags: 1028 | sum top-level fields: 1028
sum all fields: 1185
named top-level: 1002
unnamed top-level: 26
```

**Verdict: HOLDS.** Both the flattened total and the named/offset-only split reproduce exactly.
The 26 unnamed rows are bit-packed bools; `offset_only: 26` and the `## 21. Offset-only fields`
appendix account for them.

## A5 — 594 references, 466 resolved, 128 `missing-object` over 34 targets, "all `Engine.*` / `Core.*`"

**Test.** Status census in the record, plus the target list, plus a grab-wide search for the
missing names.

```
ref statuses: {'resolved': 466, 'missing-object': 128} total 594
missing_objects distinct targets: 34
{'Class': 2, 'ParticleSystem': 2, 'AkEvent': 30}
  Core.RDmgType_BatmobileCannon | Class | occurrences 7
  Core.RDmgType_BatmobileMissileBarrage | Class | occurrences 4
  Engine.Batmobile_rocketExplosion_TEMP | ParticleSystem | 1
  Engine.Play_BML_HeavyCannon_Fire | AkEvent | 4
any RDmgType anywhere in grab: []
any object with name Play_BML_HeavyCannon_Fire: []
```

**Verdict: HOLDS**, with the scope caveat spelled out below. Every missing target starts
`Core.`/`Engine.` and none of the names exists anywhere in the 20,128-row grab, so the record's
statement ("the four packages do not contain them and nothing about their values is claimed") is
accurate. Note what `missing-object` can and cannot mean: it is *not* proof the object does not
exist in JC3 — `RDmgType_BatmobileCannon` is a damage-type class that plainly does exist for the
cannon to point at. The record does not claim otherwise; §19 is titled "References that leave the
four packages", which is the correct reading.

## A6 — Reference identity is exact (the G1-08 name-only resolver bug stays fixed)

**Test.** The intent section records that G1-08 shipped a resolver that matched by last path
segment only (so every `RocketTrail` resolved to the first same-named export). Re-check the
identity of all 466 resolved refs against the target path and the export record.

```
resolved: 466 class mismatches: 0
leaf mismatches: 0
Playable_Batmobile_SF | Batmobile_Heavy_Cannon_Primary_Projectile | RBasicProjectile.ProjectileTrail ->
  Batmobile_Heavy_Cannon_Primary_Projectile.RocketTrail resolved (10, 'Projectiles.Batmobile_Heavy_Cannon_Primary_Projectile')
Playable_BatmobileMK2_SF | ... resolved (10, ...)   Playable_BatmobileFunhouse_SF | ... resolved (10, ...)
```

**Verdict: HOLDS.** Zero class mismatches, zero leaf mismatches, and each projectile's trail
resolves to *its own* component with the matching `outer`. The index-based path (G1-09's fix) is
what is on disk; the G1-08 numbers (466/128) survive the correction unchanged, as the intent
predicted.

## A7 — "0 of 1,065 comparisons differ" is a real comparison, not an empty one

**Test.** Two parts. First, read the comparison's signature function: `signature()` serialises
`ref` / `value` / `struct` / `array`, so values — not just field names — are compared. Second,
recompute independently from the raw grab (not from `WEAPONS.json`) for shared weapons:

```
Batmobile_Cannon_V2 non-ref values: 32 differences: 0
Batmobile_Heavy_Cannon_Primary non-ref values: 15 differences: 0
```

and confirm what *does* differ between packages is only the per-package export index:

```
DIFF {"offset": 2424, "ref": "Particles.Batmobile_Muzzleflash_NoTracer", "value": 4944}
  vs {"offset": 2424, "ref": "Particles.Batmobile_Muzzleflash_NoTracer", "value": 4995}
```

**Verdict: HOLDS.** The raw tag-level differences are index renumbering with identical target
paths, which is exactly what the record says it compares (by path, not index). The arithmetic also
closes: 332 union fields, of which the two 4-instance groups hold 69 (67 + 2), so
3 × 263 + 4 × 69 = 1,065.

## A8 — The fleet-wide wording is scoped to what was tested

**Test.** Which names have how many instances, and where.

```
distinct names: 24 | instances-per-name histogram: {3: 16, 4: 2, 1: 6}
Batmobile_Booster / Batmobile_Cannon_V2 -> 4 packages
6 single-instance names -> Playable_BatmobileJoker_SF only (5 Joker objects + the class default)
```

**Verdict: HOLDS.** "The base, MK2 and Funhouse packages are value-identical for every *shared*
weapon" is literally what was measured: 18 multi-instance groups out of 24 names, the 6
single-instance Joker names excluded by construction and named as such. The claim is not a
sample standing in for the fleet — it is every shared object, all instances.

## A9 — "10 projectile names, 9 launcher targets, 1 unfired"

**Test.** Grep the whole grab for any carrier of the bare `Batmobile_EMPMissile_Projectile`
(the only `fired_by: []` entry), separate from the `_ForCars` variant:

```
18 EMPMissile_Projectile            (3 object names + their outers/paths across 3 packages)
15 EMPMissile_Projectile.RocketTrail
12 EMPMissile_Projectile.Mesh0 / .CollisionCylinder / .RB_RadialImpulseComponent / .DefaultAkAudible_
```

and read the launcher that *does* name an EMP missile:

```
RBatmobileEMPMissile.ProjectileForCarsArchetype -> Projectiles.Batmobile_EMPMissile_Projectile_ForCars | resolved
RPursuitModeMissileLauncher.ProjectileArchetype -> Projectiles.Batmobile_EMPMissile_Projectile_ForCars | resolved
```

**Verdict: HOLDS**, within the stated universe. Both launcher fields point at the `_ForCars`
variant; nothing in the 20,128-record grab points at the plain one. The .md words this exactly
right — "`-` (no launcher in these packages)" — so it is a package-scoped fact, not a claim about
the game. Each projectile name lives in three packages (the Joker ones in one), so "9 launcher
targets" counts names, not objects; the record's `projectile_instances: 26` keeps the two readings
apart.

## A10 — The unit line ("cm / cm/s / 16-bit angles")

**Test.** Search for any local decode that establishes the convention, and check whether the
record converts anything.

```
Research/BatmobileGrab/PHYSICS.md:3  ... extents and local centre in centimetres (1 uu = 1 cm).
Research/BatmobileGrab/CAMERA.md:34  ... is centimetres; the `DrivingCamera*Factor` fields are scalars.
Research/BatmobileGrab/WEAPONS.md:15 ... Unreal units are centimetres for positions, cm/s for
  speeds and 16-bit angle units for rotators (65,536 = 360 degrees); nothing is converted here.
```

**Verdict: WEAK — conventional, not decoded.** The line is external UE3 knowledge, imported. It
is consistent with every other record in the project (`PHYSICS.md`, `CAMERA.md`, `MODES.md`,
`SOCKETS_JC3.md` all state the same convention) and it is inert here: no value is converted and
every number in the record is the cooked package's own float, so a wrong unit label would
mislabel, not corrupt, the data. R4 asks for provenance; the provenance for this one line is
"project convention", not a measurement.

## A11 — Undecoded arrays: "the element bytes are not in the grab"

**Test.** Open the raw rows for the two socket arrays.

```
RAW Playable_BatmobileFunhouse_SF Batmobile_EMP_Missile_Launcher MissileLaunchSockets
    {'array_index': 0, 'count': 2, 'name': 'MissileLaunchSockets', 'offset': 2572, 'size': 20, 'stride': 8, 'type': 'ArrayProperty'}
RAW Playable_BatmobileJoker_SF Batmobile_JokerMissile_Launcher MissileSockets
    {'array_index': 0, 'count': 10, 'name': 'MissileSockets', 'offset': 2608, 'size': 84, 'stride': 8, 'type': 'ArrayProperty'}
```

No `children` key on either. **Verdict: HOLDS.** The grab carries the header only, so
"recorded as undecoded rather than guessed" is the only honest option available from these inputs.
This is a real gap against the card's Do step 2 (which names `MissileLaunchSockets`), and the
record says so instead of filling it.

## A12 — "The Joker package shares three objects (`Cannon_V2`, `Booster`, `EMP_Burst`)"

**Test.** Where does each shared name actually live?

```
EMP_Burst packages: ['Playable_BatmobileFunhouse_SF', 'Playable_BatmobileMK2_SF', 'Playable_Batmobile_SF']
Joker objects: ['Batmobile_Booster','Batmobile_Cannon_V2','Batmobile_JokerCannon_V2',
                'Batmobile_JokerHeavy_Cannon','Batmobile_JokerHeavy_Cannon_Projectile',
                'Batmobile_JokerMissile_Launcher','Batmobile_JokerMissile_Projectile',
                'Default__RBatmobileMissileLauncherJoker']
```

**Verdict: BROKEN (prose only).** `Batmobile_EMP_Burst` is not in the Joker package; the Joker
shares **two** objects with the other packages and carries six names of its own (five objects plus
the class default). The artefact is right — `joker_only_objects: 5`, and `variant_map` gives
`EMP_Burst` three instances — so the error is confined to the MODLOG sentence, which no script
regenerates.

## A13 — "`objects.jsonl` 20,128 records and `CHAIN.json` 8,595 bindings"

**Test.**

```
$ wc -l Research/BatmobileGrab/objects.jsonl
20128 Research/BatmobileGrab/objects.jsonl
CHAIN.json: {'sdk_classes': 41, 'objects_bound': 105, 'named_bindings': 9225,
             'offsets_cross_checked': 336, 'cross_check_conflicts': 0,
             'ambiguous_bitfields': 0, 'still_unnamed': 0}
```

**Verdict: BROKEN (one number, prose only).** The object count reproduces exactly. The binding
count does not: `CHAIN.json` reports 9,225 named bindings, not 8,595 — the chain was extended after
G1-08 was written, so the done section carries a stale figure. The artefact is unaffected: the
script reads names from the chain, never its totals, and `--check` still passes.

## A14 — Three `ObjectNCRProperty` rows sit outside the 594

**Test.** Every object-reference field row, whether or not it became a `reference`.

```
ObjectNCRProperty field rows: 597 | with ref: 594
NCR rows without ref: [('Projectile.MyDamageType', 0), ('Projectile.MyDamageType', 0), ('Projectile.MyDamageType', 0)]
```

**Verdict: WEAK — silent but correct.** Index 0 is the UE3 null reference, so there is no target
to resolve or list; dropping them is right. The record just does not say that three nulls exist, so
a reader comparing "597 NCR fields" (countable from the field rows) with "594 references" has to
work out the difference. No behaviour or value is claimed from them.

## A15 — Card-named quantities: lifetime and inaccuracy-vs-heat are 0

**Test.** Read §5 of the .md (the card's quantity index) and look for the two:

```
- **projectile lifetime** (0): no field in these objects carries this name.
- **inaccuracy-vs-heat** (0): no field in these objects carries this name.
- **inaccuracy-vs-time** (4): ... InaccuracyVsTime.Points, ...Upgrade.Points
```

and the points themselves:

```
| `InaccuracyVsTime.Points` | 0x0000 | ArrayProperty | array, 4 items: [0.0,0.0,0.0,0.0,"CIM_Linear"]; [0.5,...]; [1.5,1.5,...]; [2.5,3.0,...] |
```

**Verdict: WEAK — gap against Do step 2, honestly reported.** The card asks for "speed,
acceleration, lifetime" and "inaccuracy-vs-time and inaccuracy-vs-heat curves with every point".
The time curve is delivered with all four points; lifetime and the heat curve resolve to zero
fields. That may be because they exist only as native class defaults (the card's own `Stop` rule
covers that: record `native`, continue) — but the record says "no field carries this name", which
is a weaker, verifiable statement than "the value is native". No value is invented, so R4 is safe;
the card's Do list is not fully delivered.

## A16 — The class-default export is counted as one of the "62 objects"

**Test.**

```
RBatmobileMissileLauncherJoker (2 obj)
    Batmobile_JokerMissile_Launcher     class_default=False fields=16
    Default__RBatmobileMissileLauncherJoker  class_default=True  fields=9
counts: gadget_objects 36, projectile_objects 26
```

**Verdict: WEAK — disclosed, but the noun is loose.** `Default__…` is the class-default object,
not a placed archetype with runtime behaviour, so "62 objects / 36 gadget objects" counts 61 real
archetypes plus one CDO. The record flags it (`class_default`, and `variant_map` skips it), and the
9 fields are harmless names, but a reader doing arithmetic on "36 gadget objects" should know that
one of them is the default object.

---

## Spot-checks

| value in the record | where verified | result |
|---|---|---|
| **62** objects, **13** classes (18/18/18/8 per package) | independent selection over `objects.jsonl`; per-package counter | agree |
| **1,028** tags → **1,185** fields; **1,002** named / **26** offset-only | recomputed from `WEAPONS.json` field rows and `offset_only` | agree |
| **594** refs = **466** resolved + **128** missing over **34** targets | status census; `missing_objects` length; every target `Core.`/`Engine.` | agree |
| **1,065** comparisons, **0** differing, **332** union fields | read `variant_map()`; 3×263 + 4×69 = 1,065; raw grab diff = index-only | agree |
| `RBatmobileCannon.ChainGunDamage` = **40** (Cannon_V2) / **999** (JokerCannon_V2) | raw `objects.jsonl` tags, all four packages | agree (MODLOG's "Joker-only 999" is correct) |
| **10** projectiles, **9** launcher targets, **1** unfired | `fired_by` lists; grab-wide grep for the bare projectile name | agree |
| `InaccuracyVsTime.Points` = **4** points | raw struct in `objects.jsonl`; .md §8 table | agree |
| **9,225** vs **8,595** chain bindings | `CHAIN.json` `named_bindings` | **disagree** (A13) |
| **Joker shares 3** incl. `EMP_Burst` | `EMP_Burst` packages | **disagree** (A12) |

## What would move this from "sound" to "tight"

1. Correct the two MODLOG sentences (Joker shares **two** objects; `CHAIN.json` now reports
   **9,225** named bindings) — prose only, no regeneration needed.
2. Say in §0 that `missing-object` means "not in the 20,128-record grab", and that three
   `Projectile.MyDamageType` rows are null references (index 0), which is why 597
   `ObjectNCRProperty` rows carry 594 references.
3. Either decode `MissileLaunchSockets` / `MissileSockets` at the reader level (the card's Do step
   2) or move that item explicitly into the G1-09/G1-13 gap list so "every value the card names"
   is not read as complete.
