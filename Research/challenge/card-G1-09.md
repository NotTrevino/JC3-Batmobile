# Assumption challenge — G1-09 · Projectiles and explosions

Challenger: Freebuff (did not write this card). Date: 2026-10-30. Read-only: nothing under
`GRAB_BACKLOG.md`, `MODLOG.md`, `Tools/`, `Working/`, the rest of `Research/` or the game install
was written or launched. This report is the only file written.

Inputs read: `GRAB_BACKLOG.md` §0.5 (R1–R14), the G1-09 card (§5, line 406), the §12 row
(line 1277), `MODLOG.md` §"G1-09 · Projectiles and explosions — intent" (line 7884) and
§"G1-09 · Projectiles and explosions — done" (line 7911), the outputs
`Research/BatmobileGrab/WEAPONS.md` §0/§4/§5, `WEAPONS.json`, the generator
`Tools/scripts/grab_weapons.py`, and the four inputs the card names (`WEAPONS.json`,
`objects.jsonl`, `PARTICLES.json`, `CHAIN.json`) plus `BMSDK_OFFSETS.json` as the independent
name evidence.

## VERDICT

**The pass gate is green and the counts reproduce exactly, but one displayed value is
mis-attributed (a broken R5 label on the `0x0420` bool), and the record's central weakness is one
it half-admits: most flight numbers are not the projectile's values, they are the fields the
archetype happens to override.** Ten of ten projectiles, 26 instances, 9 launcher targets, 1
unfired, 30 FX rows, 12 AkEvent rows and `--check` all re-derive; two consecutive reads of
`objects.jsonl` give byte-identical results.

What breaks:

- **"homing flag (unnamed bool) = true"** for `Batmobile_Tracker_Projectile` and
  `Batmobile_JokerMissile_Projectile`. `RBatmobileMissile` offset `0x0420` is a five-flag bool
  word (`bHoming` mask **1**, `MustHitTarget` 2, `GroundHugging` 4, `bForceExplodeAtTarget` 8,
  `bDisableAllCollision` 16 — `BMSDK_OFFSETS.json`). The cooked tags carry `bits: 2` (tracker =
  `MustHitTarget`) and `bits: 24` (= `bForceExplodeAtTarget|bDisableAllCollision`). **`bHoming` is
  set in neither.** The row also contradicts the record's own §0 rule that a bit-packed bool
  "cannot be named from an offset".

What is weak (disclosed or silent, none of it invented):

- **The base missile — the one WPN-3 actually fires — has no speed at all.** 4/10 rows have no
  `Projectile.Speed`, 6/10 no `MaxSpeed`, 5/10 no acceleration, 6/10 no homing flag; the class
  layout *does* declare those fields (`Projectile.Speed` 0x29C, `MaxSpeed` 0x2A0), and no
  `Default__RBasicProjectile` / `Default__RBatmobileMissile` exists in any of the 15 packages, so
  the inherited value is not recoverable from the grab. The table's `-` reads as "no value"; the
  honest reading is "the class default, unread".
- **"damage 50/60/75/250" is pre-multiplier damage.** `G1-14`'s own record
  (`DAMAGE_RULES.md` §7) states the per-`DamageType` multipliers live in the damage classes and
  were not opened, so using 50 as the HP the bar loses assumes a multiplier of 1.
- **"Explosion" is delivered as a particle reference only.** No explosion actor class exists in
  the 15 packages (`RB_RadialImpulseComponent` ×29 and `RVisualDamageComponent` ×4 are the only
  damage/impulse-named classes), which is true but is a statement about *four weapon packages*,
  not about the game.
- **The unit line is right and corroborated, but it makes one decoded number implausible**: the
  Joker missile's `Speed 500` = 5 m/s (18 km/h) with `MaxSpeed 1000` = 10 m/s.

Two more edges worth naming before anyone builds from this: the rig carries **eight `mine`
sockets** (`SOCKETS_JC3.md` lines 110–117) with **no mine projectile archetype anywhere in the
grab**, and the EMP row's data cannot carry WPN-4's "disables vehicles" at all.

```
$ python Tools/scripts/grab_weapons.py --check
ok E:\Modding\JustCause3\JC3-Batmobile\Research\BatmobileGrab\WEAPONS.json
ok E:\Modding\JustCause3\JC3-Batmobile\Research\BatmobileGrab\WEAPONS.md
PASS: 62 objects, 13 classes, 594 references (128 missing-object), 0 variant differences,
10 projectiles (9 launcher targets, 1 unfired), 30 FX rows, 12 AkEvent rows
EXIT=0
```

Both files still carry their `Oct 24 20:03` mtime after the check, so `--check` is read-only as
claimed. The card's Done criterion — "every projectile referenced by a launcher in G1-08 has a
row" — is met literally (9/9), and is answered in A2/A3 below, where its limits are.

---

## A1 — "The four vehicle packages carry 10 projectile archetypes over 26 instances" is the whole projectile set

**Test.** Class census of the four packages, then of all 15 packages in the grab, for anything
that behaves like a projectile.

```
projectile/missile classes in the 4 packages:  RBasicProjectile 13, RBatmobileMissile 13,
RBatmobileEMPMissile 3, RBatmobileMissileLauncher 3, RBatmobileMissileLauncherJoker 2,
RJokerMissileTarget 1
projectile/missile classes anywhere in objects.jsonl (all 15 pkgs): only RBasicProjectile and
RBatmobileMissile objects exist — 4+4+4 / 1 per package, total 26
Default__ objects in the 4 packages: 7, none of them a projectile class
```

Per-package instances: Batmobile 8, MK2 8, Funhouse 8, Joker 2 = **26**; names 8×3 + 2 = **10**.
The 11 `_Std_*` packages hold only materials/textures/`RAddContentBatmobileMesh` (132 objects
total), so the four-package scope is not hiding a second weapon set.

But the rig expects a projectile family the grab does not carry:

```
$ grep -n -i "mine" Research/BatmobileGrab/SOCKETS_JC3.md
110:| `Mine1` | `Batmobile_Rig_Weapons_Projectile_Mine_01` | ... | weapons | mine | ...
117:| `Mine8` | `Batmobile_Rig_Weapons_Projectile_Mine_04` | ... | weapons | mine | ...
(8 rows, 4 mine bays + 4 covers, parent `Batmobile_Rig_Weapons_Turret_Top`)
```

and those bones are animated in eight sequences (`ANIMATIONS.md`, `Batmobile_V2_Tank_Spin`,
`_Cannon_Fire`, `_ChainGun_Spin`, …). No `*Mine*` object or class exists in any of the 15
packages (`grep` over names and classes: 0 hits).

**Verdict: HOLDS for the sentence as written, WEAK as an implicit "no other Batmobile projectile
exists".** 26/10 is exact and the scope is complete *for the objects the packages contain*; the
mine bays are a projectile-carrying feature with no archetype in scope, so the set is complete
only up to the packages, not up to the car.

## A2 — "9 launcher targets, 1 without one" — the EMP missile is unfired

**Test.** Every tag in all 20,128 records of all 15 packages whose `ref_class` is
`RBasicProjectile`/`RBatmobileMissile`, or whose ref name ends `_Projectile`.

```
Projectiles.Batmobile_EMPMissile_Projectile_ForCars  <- RBatmobileEMPMissile / ProjectileForCarsArchetype,
                                                        RPursuitModeMissileLauncher.ProjectileArchetype
Projectiles.Batmobile_Heavy_Cannon_BodyShot_Projectile        <- RBatmobileHeavyCannon
Projectiles.Batmobile_Heavy_Cannon_Fully_Upgraded_Projectile  <- RBatmobileHeavyCannon
Projectiles.Batmobile_Heavy_Cannon_HeadShot_Projectile        <- RBatmobileHeavyCannon
Projectiles.Batmobile_Heavy_Cannon_Primary_Projectile         <- RBatmobileHeavyCannon
Projectiles.Batmobile_JokerHeavy_Cannon_Projectile   <- RBatmobileHeavyCannon (Joker)
Projectiles.Batmobile_JokerMissile_Projectile        <- RBatmobileMissileLauncherJoker
Projectiles.Batmobile_Missile_Projectile             <- RBatmobileMissileLauncher
Projectiles.Batmobile_Tracker_Projectile             <- RBatmobileVehicleTracker
names referenced: 9 | refs: 26
```

`Batmobile_EMPMissile_Projectile` appears in **no** reference anywhere in the grab. Its own
class's CHAIN bindings confirm the launcher points at the `_ForCars` sibling
(`RBatmobileEMPMissile.ProjectileForCarsArchetype` 0x09BC → 5206,
`RPursuitModeMissileLauncher.ProjectileArchetype` 0x097C → 5206), and no second
`ProjectileArchetype` exists on the EMP launcher. A `NameProperty`/`StrProperty` sweep for
projectile names found no indirect reference either.

**Verdict: HOLDS.** "Unfired" is exact for these 15 packages. The limit is that the negative is
only testable inside the grab: import tables of packages outside it (levels, scripts, other
actors) are not on disk, so "nothing in the game fires it" is UNKNOWN, not proven.

## A3 — "Every projectile referenced by a launcher in G1-08 has a row" (the Done check)

**Test.** The 9 targets above are exactly the 9 rows that carry `fired_by` in `WEAPONS.json`, and
the 10th row (`Batmobile_EMPMissile_Projectile`) is the flagged one.

```
projectile_coverage: launcher_targets = 9 names, unfired = [Batmobile_EMPMissile_Projectile],
                     orphan_refs = []
```

**Verdict: HOLDS, and is nearly vacuous.** It holds because only launcher objects reference
projectiles at all (no projectile references another projectile, so there is no cluster/sub-munition
chain to chase). It would not catch a projectile spawned natively or fired from a weapon outside
the 62-object selection — and A1 shows a family (mine) that has no launcher here.

## A4 — The `fired_by` field names are the launchers' real fields

**Test.** Those projectile tags are **unnamed in the stream** (the grab shows `"name": null"` for
all 26 projectile refs); every path printed in §4 comes from `CHAIN.json`'s offset→SDK-name join.
Their correctness was checked against the objects they point at:

```
Batmobile_Heavy_Cannon_Primary (RBatmobileHeavyCannon) at 0x0A??:
   ...UpgradedBodyShotProjectileArchetype -> Batmobile_Heavy_Cannon_BodyShot_Projectile
   ...UpgradedHeadShotProjectileArchetype -> Batmobile_Heavy_Cannon_HeadShot_Projectile
   ...BothUpgradesProjectileArchetype     -> Batmobile_Heavy_Cannon_Fully_Upgraded_Projectile
   ...ProjectileArchetype                 -> Batmobile_Heavy_Cannon_Primary_Projectile
RBatmobileMissileLauncher.MissileClass (0x0994) -> Batmobile_Missile_Projectile
RPursuitModeMissileLauncher.ProjectileArchetype (0x097C) -> _ForCars / Tracker
```

**Verdict: HOLDS.** Four offsets ⇒ four targets whose own names are the same four words, which is
the only independent confirmation available when the stream carries no name. This also means the
whole `fired_by` column rests on the BmSDK layout matching the cooked offset table — correct here
(4/4, plus the 3 missile fields), but it is an inference from names, not a behaviour trace.

## A5 — Unit convention: "cm, cm/s, 16-bit angles; nothing is converted"

**Test.** The convention *is* documented (§0, lines 15–16), so it is not silent. Corroborated
against numbers on disk from other writers:

```
RBatmobileMissileLauncher.LockOnRange     = 12000  -> 120 m   (plausible)
RBatmobileMissileLauncher.LockOnAngle     = 40     -> 40 deg  (plausible)
RBasicProjectile.InitialAcceleration      = [0,0,-1000] -> -10 m/s^2 (~1 g)
RBatmobileMissile.HomingDelay (tracker)   = 0.2    -> 0.2 s  (not stated as seconds anywhere)
```

Applied to the projectiles:

| projectile | speed | max | accel | reading |
|---|---:|---:|---:|---|
| heavy cannon primary | 40000 | 48000 | −1000 z | 400 / 480 m/s |
| Joker heavy cannon | 10000 | 12000 | −1000 z | 100 / 120 m/s |
| EMP missile | – | 7500 | 40000 | 75 m/s, 400 m/s² |
| tracker | – | 20000 | 30000 | 200 m/s, 300 m/s² |
| Joker missile | 500 | 1000 | 8000 | **5 / 10 m/s** |
| base missile | – | – | – | none |

**Verdict: HOLDS for the convention, with two unnamed units (cm/s² for acceleration, seconds for
the delays) and one coherence flag.** 5 m/s is slower than Rico sprints; the only alternative
reading (metres) is excluded by `LockOnRange` 12000 = 120 m, so the number is decoded correctly and
the oddity is in the content, not the conversion. One probe in phase Q, not a rewrite.

## A6 — A row's numbers describe the projectile's flight (absent ⇒ inherited, not zero)

**Test.** Class layouts vs what each archetype serializes.

```
BMSDK_OFFSETS.json Projectile: Speed 0x29C, MaxSpeed 0x2A0, Damage 0x2D8, DamageRadius 0x2DC,
                              MomentumTransfer 0x2E0  (class size 744)
objects.jsonl Batmobile_Missile_Projectile tags at 0x29C/0x2A0/0x428: none
objects.jsonl Batmobile_EMPMissile_Projectile: MaxSpeed 7500, AccelRate 40000 — no Speed
objects.jsonl Batmobile_Tracker_Projectile: MaxSpeed 20000, AccelRate 30000 — no Speed
no Default__RBasicProjectile / Default__RBatmobileMissile export in any of the 15 packages
```

**Verdict: WEAK.** The record says "whether a class default supplies it is not claimed", which is
honest and R4-safe, but the table renders the four cases identically (`-`), and a translator reading
"base missile: speed absent" and "Joker missile: speed 500" has no way to see that both derive from
an unread default of the same class. The consequence is concrete: **WPN-3's missile, WPN-4's EMP
missile and the tracker have no decoded flight speed at all**, and the tracker's `MaxSpeed 20000`
plus `HomingDelay 0.2` are only half a trajectory. Flight values must stay `UNKNOWN` (`blocked` in
T-11) until a CDO dump exists — not `decoded (fleet)`.

## A7 — "homing flag (unnamed bool) = true" on the tracker and the Joker missile

**Test.** `RBatmobileMissile` declares one bool word at 0x420:

```
BMSDK_OFFSETS.json  RBatmobileMissile 0x420 (1056), five BoolProperties, one mask each:
  mask 1  bHoming                mask 2  MustHitTarget      mask 4  GroundHugging
  mask 8  bForceExplodeAtTarget  mask 16 bDisableAllCollision
objects.jsonl, the projectile's only 0x420 tag:
  Batmobile_Tracker_Projectile     {"bits": 2,  "offset":1056, "type":"BoolProperty", "value":true}
  Batmobile_JokerMissile_Projectile{"bits": 24, "offset":1056, "type":"BoolProperty", "value":true}
  every other projectile: no tag at 1056 at all
```

`bits` is a mask, not an index (24 = 8|16; the same field type is `8421464` and `2617246740` on
Actor bool words). So:

- tracker: `MustHitTarget = true` and **`bHoming = false`** — a tracking missile that must hit its
  target, not one flagged as homing.
- Joker missile: `bForceExplodeAtTarget = true`, `bDisableAllCollision = true`, `bHoming = false`.
- All others: the flag word is unserialized; `bHoming` may be set in the class default — UNKNOWN.

The record's own §0 says a packed bool "cannot be named from an offset", then §4 prints
"homing flag (unnamed bool)" with `true` for both. `WEAPONS.json` drops the `bits` in the
projectile projection (`"homing_flag": {..., "value": {"value": true}}`), so nothing downstream can
recover which flag it was.

**Verdict: BROKEN.** Correct data, wrong label, and the label loses the behaviour that actually
matters (must-hit vs force-explode-at-target vs collision off). This is exactly R5: the member whose
name sounded closest, not the member whose bit is set.

## A8 — "No projectile carries `LifeSpan`/`Lifetime`"

**Test.** All 26 instances, every tag offset:

```
projectile tags at 0x15C (348, Actor.LifeSpan) or 0x164 (356): 0
BMSDK_OFFSETS.json Actor: LifeSpan FloatProperty 0x15C   (212 properties, size 668)
Projectile class: no LifeSpan/Lifetime property; Projectile class size 744 ends at 0x2E8
```

**Verdict: HOLDS as written, with one correction of the sentence that follows it.** No
`Projectile.LifeSpan`/`Lifetime` exists in the class at all, and no archetype overrides
`Actor.LifeSpan`. So "the field is absent" is a *class-level* fact, not a gap — but "projectiles
have no lifetime" is not proven either: they inherit `Actor.LifeSpan` from the CDO, value unread.
`FOOTAGE.md` F-1's `UNKNOWN` for flight time stands, and a footage measurement remains the only
source.

## A9 — "damage 50 / 60 / 75 / 250" is the damage dealt

**Test.** `Projectile.Damage` values vs the damage-type chain and `G1-14`'s findings.

```
primary cannon 50.0 (turret 75)   body shot 75.0 (turret 110)   head shot – (turret 110)
fully upgraded 75.0 (turret 110)  EMP 60.0 (RDmgType_BatmobileCannon)
base missile 250.0 (RDmgType_BatmobileMissileBarrage)   Joker missile 250.0   tracker –
DAMAGE_RULES.md §7: "The per-DamageType multipliers live in the damage classes ... those classes
are engine-side and were not opened here."   §3.5: the multiplier is absent from the archetype.
```

**Verdict: WEAK.** The numbers are decoded, but a damage *value* is not a damage *outcome*: HP
lost = `Damage × multiplier(DamageType) × mode factor`, and both factors are UNKNOWN. Two further
name-level readings travel with the numbers: "turret-shot damage" is the SDK's name for a second
damage value whose trigger (turret shot? tank-mode shot? hit location?) is not proven, and the four
heavy-cannon archetypes differ by *hit location* and *upgrade level*, so "the cannon does 50" is one
of up to four values selected by code. Do not let T-11 carry `50` as a buildable class value.

## A10 — "`Projectile.DamageRadius` 0.0" means no splash

**Test.** The missile's radial machinery:

```
Batmobile_Missile_Projectile: DamageRadius 0.0, MomentumTransfer 25000,
  ImpactRadialImpulseComponent -> ...ImpulseComponent0 (RB_RadialImpulseComponent)
Joker missile:                 DamageRadius 300.0
Joker heavy cannon:            DamageRadius 350.0
ImpulseComponent0 of the primary cannon: ImpulseFalloff "RIF_Constant",
  0x0220 = 15000.0, 0x0234 -> Core.RDmgType_Explosion
```

**Verdict: WEAK.** The decoded zero is correct, but the AOE story is not where the record says:
the primary cannon carries a radial impulse component with an *explosion* damage type and a
constant falloff while its `DamageRadius` is also `0.0`, and the missile has a full radial component
with `DamageRadius 0.0`. "Radius 0" therefore does not mean "no radial effect" — the radius would
be inside `RB_RadialImpulseComponent`, which has no named fields here (A12). Anyone building FX-2/WPN-3
splash from `DamageRadius 0.0` would build no splash.

## A11 — "`ExplosionTemplate` is a ParticleSystem, not an explosion actor; the packages hold no explosion damage/radius actor values"

**Test.** Every class in all 15 packages whose name contains explod/blast/damage/impulse/radial:

```
RB_RadialImpulseComponent 29   RVisualDamageComponent 4      (nothing else)
ExplosionTemplate tags: object refs, ref_class ParticleSystem (all 4 missile families)
Engine.Batmobile_rocketExplosion_TEMP (Joker cannon impact): not an export anywhere, not in
PARTICLES.json either -> missing-object, correctly
Engine.Batmobile_Rocket_Trail (3 missile families): absent from PARTICLES.json (206 systems,
  only the 4 weapon packages) -> missing-object, correctly
```

**Verdict: HOLDS as scoped, WEAK as a statement about explosions.** The sentence is explicitly
"in these packages" and that is true. But the card's title is *projectiles and explosions*, and the
explosion half of it reduces to particle-system references — no explosion damage, radius, impulse
or audio is decoded, and the places they could live (the `Core.RDmgType_*` classes, the 117
`Engine.*` imports, the 11 `Core.*` imports, the mine family) were not opened. A reader should
treat "explosions" in G1-09 as `FX-2` only; explosion damage stays UNKNOWN.

## A12 — "`ImpulseComponent0` values: 15000 / 1000 / 500" are impulses

**Test.** Is there any name evidence for the component's fields?

```
BMSDK_OFFSETS.json classes (41): no RB_RadialImpulseComponent
WEAPONS.md: "Impulse component" tables list `offset 0x0220`, `offset 0x016C`, `offset 0x0190`
MODLOG G1-09 done: "...its ImpactRadialImpulseComponent to ...ImpulseComponent0 with the 15,000
impulse - not the EMP missile's 1,000."
```

The values themselves:

```
offset 0x013C 268? replacement primitive (all)     0x0220: primary 15000, EMP 1000, Joker cannon 500
0x021C ImpulseFalloff "RIF_Constant" (primary)     0x0234 -> Core.RDmgType_Explosion (primary)
0x016C: present in EVERY component, values 0.9754, 0.9299, 0.8149, 0.6686, 0.5830, 0.5090,
        0.4082, 0.3269, 0.2469, 0.0902 — including the EMP burst's (0.9155), which has no 0x0220
```

**Verdict: WEAK.** `WEAPONS.md` obeys the G1 rule (offset label, value, no invented name), but
the MODLOG sentence and the value rows present 15000 as an impulse magnitude with no evidence, and
a "radius" reading (150 m) is equally consistent with the bytes. The unnamed `0x016C` float is
printed with the same weight as the round numbers and looks like tuning or noise, not a quantity to
build with. Nothing here is buildable until the component class is dumped.

## A13 — "0 / 1,065 variant comparisons differ"

**Test.** Full-tag comparison of all 26 instances, including unnamed fields the 1,065 comparison
may skip:

```
Batmobile_EMPMissile_Projectile        inst=3 identical_tag_shape=True identical_values=False
Batmobile_Heavy_Cannon_Primary_...     inst=3 identical_tag_shape=True identical_values=False
Batmobile_Tracker_Projectile           inst=3 identical_tag_shape=True identical_values=False
Batmobile_JokerHeavy_Cannon_Projectile inst=1 ... True/True
projectiles compared: 10, with differing values: 8
```

Every difference is a per-package export/import index (`5067` vs `5027` vs `4976`;
`Core.RDmgType_BatmobileCannon` = −104 in Funhouse vs −121 in MK2/base), i.e. identity, not value.
After that normalisation every decoded scalar and bit word is identical across packages, and the
only structural gap is the homing word (A7), which is identical where it exists.

**Verdict: HOLDS**, verified harder than the record's own check.

## A14 — "Emitter counts from `PARTICLES.json`" in the FX rows

**Test.** Re-read every system the §4 FX rows name, with stub emitters counted separately:

```
Batmobile_HeavyCannon_Impact  8 / 5 emitters (doc: 8 and 5)          stubs 0 / 0
Batmobil_Rocket_Explosion     14 emitters (doc: 14)                  stubs 6
Batmobil_Rocket_Explosion_Small 9 (doc: 9)                           0
FireTrail_APC 10, FireTrail_Car 9, Batmobile_CanonTrail 2, Batmobile_JokersRocket_Trail 4
Trail_Body_UPGR 4 (doc 4) -> 1 stub;  Trail_Full_UPGR 4;  Trail_Head_UPGR 3
Muzzle 7/9/7, Impact 14/16/14 (doc agrees)
```

**Verdict: WEAK (cosmetic).** Every count matches, but the counts include stub emitters
(`kind: none`, no modules, `lod_levels: 0`): `Batmobil_Rocket_Explosion` is "14 emitters / 8 live",
`Trail_Body_UPGR` "4 / 3". No claim depends on it, but "14 emitters" is template slots, not
particles.

## A15 — The EMP row can stand in for WPN-4's behaviour

**Test.** Every field of `RBatmobileEMPMissile` (`Batmobile_EMP_Missile_Launcher`) and its
projectile:

```
launcher: ProjectileForCarsArchetype, UntagWarningEvent, CantFireOnPenguinVanDialogue,
          MissileLockOnDuration 2.0, CivilianMissileLockOnDuration 1.0, LauncherAnimNodeName,
          LoseLockXBonus 600, LoseLockYBonus 800, MissileLaunchSockets (undecoded array)
projectile: max speed 7500, accel 40000, damage 60, RDmgType_BatmobileCannon, radius 0.0,
          ExplosionTemplate (particles), 3 AkEvents, radial component 0x0220 = 1000
RBatmobileEMP (the burst gadget) does carry `EMPFireSwitch` - an undecoded ArrayProperty.
```

**Verdict: WEAK.** Nothing in the EMP missile's own data says "EMP": no disable radius, no
duration, no EMP damage type (it is `RDmgType_BatmobileCannon`), and the one EMP-specific array
belongs to the *other* gadget and is undecoded. The record is honest, but WPN-4's "disables
vehicles" has **no decoded carrier at all**, and a translator could easily mistake the missile's 60
damage for the intended effect.

## A16 — The records reproduce: counts, gate, determinism

**Test.** Independent recounts and the gate.

```
counts from WEAPONS.json: objects 62, gadget_objects 36, projectile_objects 26, classes 13,
  projectile_names 10, projectile_instances 26, launcher_projectiles 9, unfired 1,
  projectile_effects 30, projectile_audio_events 12, references 594 = 466 + 128, variant
  comparisons 1065, differing 0
independent: 26 projectile exports / 10 names / 9 refs / 1 unreferenced  -> agree
$ python Tools/scripts/grab_weapons.py --check   -> PASS, EXIT=0 (files unchanged, mtime 20:03)
```

The MODLOG's claim that the old name-only join had mis-resolved every trail also reproduces: the
**first** `RocketTrail` export in `Playable_Batmobile_SF` is index 9, which is the EMP missile's, so
every other projectile's trail did resolve to the EMP's component before the G1-09 fix.

**Verdict: HOLDS.** Counts, determinism and the resolver fix are all reproduced.

---

## Spot-checks

| value in the record | where verified | result |
|---|---|---|
| **10** names, **26** instances, 8/8/8/2 per package | independent class + name census | agree |
| **9** launcher targets, **1** unfired (`EMPMissile`) | grab-wide ref sweep, all 15 packages | agree |
| heavy cannon primary **40000 / 48000 / [0,0,−1000] / 50 / 0.0 / 66666.67** | `objects.jsonl` tags + `CHAIN.json` layout | agree |
| Joker missile **500 / 1000 / 8000 / prox 100 / 250 / 300 / 25000** | same | agree |
| tracker **max 20000 / accel 30000 / HomingDelay 0.2 / MomentumTransfer 500** | same | agree |
| `_ForCars` "no scalar value at all" | 10 tags, 0 scalars, 6 object refs | agree |
| `Projectile.Damage` absent for EMP + tracker | no 0x2D8 tag in either | agree |
| **homing flag = true** (tracker, Joker missile) | same tag, bits **2** / **24** | **disagree** (A7) |
| "14 emitters" | 14 slots, **8** live | agree, overstated (A14) |
| **1,065** comparisons / **0** differences | full-tag diff of 26 instances | agree (A13) |
| `Engine.Batmobile_Rocket_Trail` missing | absent from `PARTICLES.json` too | agree |

## What would move this from "green" to "tight"

1. Fix the `0x0420` row: label it by mask (`bHoming` / `MustHitTarget` / `bForceExplodeAtTarget` /
   `bDisableAllCollision`) and keep the bits in `WEAPONS.json`. That is R5, and the behaviour
   difference between a must-hit tracker and a force-explode Joker missile is translation-relevant.
2. State in §4, once, that `-` means "the archetype does not override it; the class default is
   unread", and that no CDO export of either projectile class exists in the grab — then mark
   speed/acceleration `blocked` for WPN-3/4 rather than leaving them to the reader.
3. Add one line to §4 that `ExplosionTemplate` is FX only and that explosion damage/radius/impulse
   are UNKNOWN (A11/A12), so the card's "explosions" is not mistaken for a behaviour record.
4. Record the **mine** family (`SOCKETS_JC3.md` `Mine1…Mine8`, bones
   `Batmobile_Rig_Weapons_Projectile_Mine_0[1-4]`) as a named, archetype-less projectile gap
   instead of leaving the 10-name list to imply there is nothing else.
5. Note the pre-multiplier nature of `Projectile.Damage` (A9) with a pointer to
   `DAMAGE_RULES.md` §7 — one clause prevents a T-11 row from carrying `50` as an outcome.
