# Assumption challenge — G1-16 · Particles by feature

Challenger: Freebuff (did not write this card). Date: 2026-10-30. Read-only: nothing under
`GRAB_BACKLOG.md`, `MODLOG.md`, `Tools/`, `Working/`, the rest of `Research/` or either game install
was written or launched. This report is the only file written. All probes re-read the same inputs the
card reads (`PARTICLES.json`, `objects.jsonl`, `WEAPONS.json`, `MECHANICS.md`) plus, read-only, the
Batman: Arkham Knight packages the generator itself opens.

Inputs read: `GRAB_BACKLOG.md` §0.5 (R1–R14), the G1-16 card (§5, line 498) and its `Done` clause,
the §12 row (line 1284), `MODLOG.md` §"G1-16 · Particles by feature (intended)" (line 8387) and
§"… — done" (line 8412), the outputs `Research/BatmobileGrab/PARTICLES_FEATURES.md` (261 lines) and
`.json` (29,872 lines), and the generator `Tools/scripts/bmak_particle_features.py` (584 lines) with
its G1-6 parser `Tools/scripts/grab_particles.py`.

## VERDICT

**The numbers re-derive exactly; four of the claims that frame them do not hold.** `--check` is green
and every count in the md reproduces from the JSON (206 systems / 63 names / 1433 emitters / 1107
levels / 17 groups / 1290 colour boxes / 49 referenced names), so the pass is internally consistent
and reproducible. What breaks is what the counts are *taken to mean*: the feature groups are name
patterns, the reference set is a filtered subset that misses a card-named feature, three "absent"
features have particle components on the entity, and "no colours / no size" mixes *not present* with
*not extracted*.

| # | assumption | verdict |
|---|---|---|
| A1 | the 206 `ParticleSystem` exports are the complete, in-scope particle universe | **HOLDS** for "all exports in the 4 packages"; scope **WEAK** (3 Batwing systems) |
| A2 | a system's feature group follows from its name (first rule wins) — R5 | **BROKEN** — 8 of 16 `tracer` rows are `Muzzleflash_NoTracer` |
| A3 | the reference set (`WEAPONS.json` + `objects.jsonl` "wheel/vehicle objects") is what the Done-when means | **BROKEN** — the class-name filter drops 85/349 ref rows; `Engine.Batmobile_Rocket_Trail` is ungrouped |
| A4 | wall-scrape, speed-lines and heat-steam are absent features | **BROKEN** as reasoned (components exist on all four variants; target UNKNOWN); literal "no system by that name in the 206" HOLDS |
| A5 | systems without colours / sizes have none | **BROKEN** — 23/23 colour-less rows and 28/32 size-less rows carry the module as a cooked lookup |
| A6 | the two stored vectors are min/max bounds | **HOLDS** mechanically (0 of 1290 boxes inverted), semantic reading **WEAK**; the quoted `193/863` denominator is **BROKEN** |
| A7 | "spawn 206/206" means every system's spawn is measured | **WEAK** — 77 systems have Rate and required SpawnRate at 0/none |
| A8 | the MECHANICS wheel anchor proves the wheel refs complete | **WEAK** — circular (same grab), 8 names from 12 printed wheel rows |
| A9 | material = `ParticleModuleRequired`'s Material reference (not `PARTICLES.json`'s column) | **HOLDS** — 1018/1018 picks carry a Material-classed ref, 0 fallbacks |
| A10 | lifetime 203/206, the 3 others really have none | **HOLDS** — the 3 are `EMP_Burst_Charge`, light emitters with no lifetime module |
| A11 | every system lands in exactly one group, none in `other` | **HOLDS** — `other` = 0, rows sum 206 |
| A12 | the units/conventions (s, /s, size, colour) are known | **WEAK** — size has no unit, colour has no space, both exceed 1 by orders of magnitude |
| A13 | `--check` verifies the card's Done-when | **WEAK** — it tests group *membership* and counts, not correctness or completeness |
| A14 | MODLOG's "44 from `WEAPONS.json`" | **BROKEN** — `WEAPONS.json` yields 30 distinct names; 44 is the in-206 part of the 49-name union |

Baseline, quoted once (this is what the assertions above are measured against):

```
$ python Tools/scripts/bmak_particle_features.py --check
{"systems": 206, "distinct_names": 63, "emitters": 1433, "levels": 1107, "groups_used": 17, …}
OK: 206 systems (63 names) in 17 groups; facts: lifetime 203, spawn 206, size 174, materials 206,
colours 183 (1290 boxes); coverage 49 referenced names (44 in-grab + 5 external), 8 MECHANICS wheel
refs all found in objects.jsonl
EXIT=0
```

---

## A1 · "The 206 exports are the complete particle universe" — HOLDS (scope WEAK)

**Assumption.** `PARTICLES.json`'s 206 `ParticleSystem` rows are every particle system the Batmobile
has; anything not in them "lives elsewhere" (the 5 external refs).

**Test.** Counted `ParticleSystem` exports in `objects.jsonl` per package, which is the grab's full
export census (15 packages):

```
Playable_BatmobileFunhouse_SF 59 | Playable_BatmobileJoker_SF 29
Playable_BatmobileMK2_SF 59     | Playable_Batmobile_SF 59
total ParticleSystem exports in objects.jsonl: 206   (the 11 *Std* packages: 0)
```

**Result.** The completeness half **HOLDS**: 206 is exactly every `ParticleSystem` export in the four
packages, and the 11 `Playable_Batmobile*_Std*` packages contain none. The scope half is **WEAK**:
three of the 206 are another vehicle's systems, in the Joker variant package —

```
Batwing_Booster_CINE  | Playable_BatmobileJoker_SF | outer Particles.Vehicles      | light emitter
Batwing_Exhaust_P     | Playable_BatmobileJoker_SF | outer VFX_Vehicles.Particles  | trail
FloorDust_Batwing     | Playable_BatmobileJoker_SF | outer Particles.Vehicles      | mesh particles
```

They are counted inside `afterburner-exhaust` (12 systems) and `tyre-surface` (16) with no note, so
"the Batmobile's afterburner group has 12 systems" is 10 Batmobile + 2 Batwing, and T-17 reading
`afterburner-exhaust` can pick `Batwing_Exhaust_P` as a Batmobile exhaust. Silent, small, fixable
with a note; it does not invalidate any number, only the reading of the group totals.

## A2 · "The feature group follows from the name" — BROKEN (R5)

**Assumption (stated).** `RULES` in the generator: the first regex that matches the system *name*
wins; `other` last. The md says so ("first name rule wins") and the MODLOG treats the result as
"groups by feature".

**Test.** `python Tools/scripts/bmak_particle_features.py --group tracer` (and `--group muzzle-flash`):

```
Batmobile_Muzzleflash_NoTracer_Nv | Playable_Batmobile_SF | 0.05..1.1 | 0 | [25 25 25]..[25 25 25]
Batmobile_Muzzleflash_NoTracer    | Playable_Batmobile_SF | 0.05..1.1 | 0 | -
Batmobile_Muzzleflash_Tracer      | Playable_Batmobile_SF | 0.35..0.5 | 0 | -
Batmobile_RiotSuppressor_Tracer   | Playable_Batmobile_SF | 1        | 0 | [0.9 0.9 0]..[1.5 1.5 1.5]
   (× 4 packages)
```

**Result.** **BROKEN.** `tracer` matches before `muzzle` in the rule order, so the two systems whose
own name says **NoTracer** land in the tracer group: 8 of that group's 16 rows. `muzzle-flash` (21)
therefore excludes them — by behaviour it would be 29 and `tracer` 8. The name is the only evidence
used (no emitter kind, no reference), which is exactly what R5 forbids ("behaviour before member …
not the JC3 member whose name sounds closest"). This is the same defect for any renamed system: the
group table stays plausible and wrong, and `--check` cannot see it (A13). `role` (the G1-6 `classify`)
is the same construction — kinds first, then name tokens — so the md's `role` column is a label, not a
decoded behaviour; e.g. `Batmobile_FearGas_Burnout` reads `burnout smoke` because of the word
"burnout", not because anything in the graph says smoke.

## A3 · "The reference set is what the Done-when means" — BROKEN

**Assumption.** The card's *Done* is "every system referenced by G1-08/G1-09 or a wheel/vehicle object
has a feature group". The generator builds that set from `WEAPONS.json` (`ParticleSystem` targets) and
from `objects.jsonl` rows whose **class name** matches

```python
VEHICLE_RE = re.compile(r"wheel|vehicle|batmobile|tank|apc|drone|wing|booster|cannon|missile", re.I)
```

**Test 1 — how much the class filter drops.** Counted every `ParticleSystem` ref row in
`objects.jsonl` by the referencing object's class, marking whether `VEHICLE_RE` accepts it:

```
SVehicleWheel          True  154      ParticleSystem          False 31
RVehicleBatmobile      True   34      ParticleSystemComponent False 29
RBatmobileCannon       True   24      RBasicProjectile        False 25
RBatmobileMissile      True   16      … (all others True)
ref rows from classes the filter drops: 85 of 349          (349 - 85 = 264, the md's count)
```

**Test 2 — what the drop costs.** The union of every name referenced anywhere in the grab
(`WEAPONS.json` ∪ unfiltered `objects.jsonl`) is **65** names; the record groups **64**:

```
union of every ParticleSystem name referenced anywhere in the grab: 65
grouped (206 names + 5 external): 64 | NOT grouped: ['Batmobile_Rocket_Trail']
```

The one name is a missile trail, and it is referenced nine times, from every Batmobile projectile, in
all four package variants:

```
Playable_Batmobile_SF | ParticleSystemComponent | RocketTrail | outer Projectiles.Batmobile_Missile_Projectile
    ref ParticleSystem Engine.Batmobile_Rocket_Trail   (same for Batmobile_EMPMissile_Projectile,
    Batmobile_Tracker_Projectile; × Funhouse / MK2 / SF)
```

**Result.** **BROKEN.** `Batmobile_Rocket_Trail` is neither one of the 206 (it lives in `Engine`) nor
one of the 5 recorded externals, because its referring objects are `ParticleSystemComponent` and
`RBasicProjectile`, which the class regex rejects. It is precisely one of the card's named features
("missile trails"), so the Done-when is short by one system, and the record's "49 referenced names,
all grouped" is true only of the 49 the filter kept. The fix is a behaviour test (any object whose
refs include a `ParticleSystem`, or the component's own class), not a name regex — R5 again.

## A4 · "Wall-scrape, speed-lines and heat-steam are absent" — BROKEN as reasoned

**Assumption (stated).** md Gaps: *"Wall-scrape sparks, speed lines and heat steam have no system by
that name in the 206 — the groups are kept so the absence is a finding"*; the per-group notes add
*"wall-scrape sparks are either a material-side effect or live outside the Batmobile packages"* and
*"heat/steam is the HUD + audio side (G1-14 recorded the weapon generator heat, not a particle)"*.

**Test.** Searched `objects.jsonl` — the grab's own export census — for object **names** matching
`scrape|spark|speedline|steam`, every class:

```
Playable_BatmobileFunhouse_SF | ParticleSystemComponent | HeatSteam   | outer Vehicle.BatmobileFunhouse
Playable_BatmobileFunhouse_SF | ParticleSystemComponent | SpeedLines0 | outer Vehicle.BatmobileFunhouse
Playable_BatmobileFunhouse_SF | ParticleSystemComponent | WallScrape0 | outer Vehicle.BatmobileFunhouse
Playable_BatmobileFunhouse_SF | ParticleSystemComponent | WallScrape1 | outer Vehicle.BatmobileFunhouse
… identical rows in Playable_BatmobileJoker_SF (outer Vehicle.JokersBatmobile),
  Playable_BatmobileMK2_SF (Vehicle.Batmobile_MK2) and Playable_Batmobile_SF (Vehicle.Batmobile)
= 16 objects
```

**Result.** The literal claim **HOLDS** (no `ParticleSystem` *export* in the 206 is named
wall-scrape/speed-line/steam). The *reasoning* is **BROKEN**: each of the four variants carries
`ParticleSystemComponent` objects for exactly these three features, parented to the Batmobile entity
itself, so "heat/steam is the HUD + audio side, not a particle" and "wall-scrape sparks are either
material-side or live outside the packages" are not supported by the grab's own census. What *is*
unknown is the system each component plays: the instance row serialises only
`ReplacementPrimitive = 0` and one float, and its `refs` list is empty —

```
{"class": "ParticleSystemComponent", "name": "WallScrape0", "outer": "Vehicle.Batmobile",
 "refs": [], "native_refs": [], "tags": [{"name": "ReplacementPrimitive", "value": 0}, …]}
```

so the template is in the archetype, not the instance. Reading the template out of `Engine.upk` is not
possible here: the package is compressed (even known live names such as `Sparks_G_INST` and
`DefaultParticle` return 0 hits from a raw grep), so the honest status is **present as a component,
target system UNKNOWN** — not "absent". This is the R4 failure mode the rules name: a row with no
semantic bridge should be `UNKNOWN`, never an inferred absence with a plausible cause attached.

## A5 · "Systems without colours / sizes have none" — BROKEN

**Assumption (silent).** The summary's `systems_with_colours 183` and `systems_with_size 174`, and the
`-` cells in the md, read as "23 systems have no colours, 32 have no size". The Method describes only
the vector-pair path.

**Test.** Re-walked all 1107 levels and classified each colour/size struct a module actually carries —
`vecpair` (two `VectorProperty` children, what the pass reads), `lookup` (cooked `LookupTable`
array only), `other`:

```
colour struct shapes:  vecpair 1290 | lookup-only 654 | other 14
size   struct shapes:  vecpair  823 | lookup-only 310 | other 10

per system:
('colours', 'doc has',  'stored vecpair') 183
('colours', 'doc none', 'stored lookup')   23      <- all 23
('size',    'doc has',  'stored vecpair') 174
('size',    'doc none', 'stored lookup')   28
('size',    'doc none', 'stored none')      4      <- only these truly have no StartSize
```

A concrete case: `Batmobile_Muzzleflash_NoTracer` reports no colours, yet every level carries

```
ParticleModuleColor.StartColor  StructProperty: [ObjectNCRProperty 0, LookupTable ArrayProperty floats]
ParticleModuleColorScaleOverLife.ColorScaleOverLife  StructProperty: [ObjectNCRProperty 0,
    LookupTable ArrayProperty floats, FloatProperty 2.0, FloatProperty 0.5]
```

**Result.** **BROKEN** as a statement of fact. Every one of the 23 colour-less rows carries colour
modules; 28 of the 32 size-less rows carry a `ParticleModuleSize`. Their values are cooked lookup
tables this pass does not decode, so the correct cell is **UNKNOWN**, not "-". The card asked for
"colours over life, sizes … per system"; 183/206 and 174/206 are the extraction yield, not the data.
The Gaps section mentions neither count, so a downstream card (T-17) has no way to tell
"no colour" from "colour not extracted".

## A6 · "The two stored vectors are min/max bounds" — HOLDS mechanically, WEAK semantically, and the quoted share is wrong

**Assumption (stated).** `Walker.vec_pair`: the cooked order "is not always min-first (193 of 863
pairs are stored max-first), so the bounds are taken per component"; the md repeats that colour ranges
are the two stored vectors as component-wise bounds.

**Test 1 — does the sort work?** Every reported box checked for `min > max`:

```
inverted components: 0 | boxes: 1290 | pairs: 1290 | systems with an inverted box: 0
```

**Test 2 — the quoted ratio.** Counted the stored pairs in `PARTICLES.json` (which stores the raw
`stored` pair next to min/max):

```
all vector pairs: 1320 | non-degenerate: 739 | stored max-first in some component: 193
start_size pairs: 796 (111 max-first)
```

**Result.** **HOLDS** as an implementation (no inverted range can escape, so no consumer sees a
reversed interval). **WEAK** as a semantic claim: the artefact keeps only the sorted result, so a pair
that is genuinely (min, max) and one that is two unrelated vectors are indistinguishable in the
deliverable — and the fact that 26 % of non-degenerate pairs are stored max-first is itself evidence
that the pair's meaning is not "bounds" by construction; it is the project's consistent convention
(the same normalisation `distribution()` applies to float uniforms). **BROKEN** on the number:
`193 of 863` appears in `grab_particles.py`'s docstring and in the G1-16 MODLOG, but there are 1320
stored pairs (739 non-degenerate) — 863 matches neither. The numerator 193 is right.

## A7 · "Spawn 206/206" — WEAK

**Assumption.** `systems_with_spawn 206` and the group column `spawn /s` read as measured emission
rates; a printed `0` reads as "does not emit".

**Test.** Counted systems whose `spawn_rate` and `required_spawn` are both 0..0 or absent, and those
with any non-zero continuous rate:

```
systems whose Rate AND required SpawnRate are 0/none: 77 of 206
systems with a non-zero continuous rate:               129
examples of the 77: Anti_firearm_gel_Miss_Px, Batmobile_HeavyCannon_Impact(_Px),
Missile_LineMarker, Tank_SplashDamage_Marker, EMP_Burst_Stage_01..03, …
```

**Result.** **WEAK.** The Method does disclose it ("a 0..0 range means emission comes from the
module's burst list or from `ParticleModuleSpawnPerUnit`, which this pass does not extract"), but the
two places a reader actually quotes — the summary line and the group table — present 206/206 and `0`
as if they were measured. 77 of 206 (37 %) are UNKNOWN emission, which matters most for exactly the
bursty features the card asks for (EMP burst, impact, muzzle flash).

## A8 · "The MECHANICS wheel anchor proves the wheel refs" — WEAK

**Assumption.** The coverage table's "wheel rows printed in MECHANICS.md | 8 | … also found as
`objects.jsonl` refs | 8" is an independent confirmation that the wheel's particle references are
complete.

**Test.** The anchor scrapes `MECHANICS.md` lines containing `ParticleSystem ×`, collects the dotted
paths, and then requires each name to also appear as an `objects.jsonl` ref:

```
| Playable_Batmobile_SF | `WheelFL` | 191 | ParticleSystem ×12 | `Engine.Batmobile_Burnout`;
  `Engine.Water_Splash`; `Engine.tyreMarks_ribbonTest`; `Impacts.Batmobile_Wheels_Wood_Collision`;
  `Mud.Batmobile_Mud_Trail`; `Particles.Batmobile_Burnout_MUD` |
… 13 wheel rows over the four packages (Joker prints one; the others four each)
distinct names collected: 8   (5 in the 206 + 3 external)
```

**Result.** **WEAK.** Both sides derive from the same grab, so the comparison proves the two files
agree, not that the set is complete — and the "8 wheel rows" label is wrong twice over: `MECHANICS.md`
prints **13** wheel rows (`grep -c 'ParticleSystem ×' Research/BatmobileGrab/MECHANICS.md` → 13),
and what the anchor counts is 8 distinct *system names*. The wheel rows also
show a per-wheel count the record never reconciles: `ParticleSystem ×12` / `×13` components per wheel
versus 6 distinct names — the other slots are repeats or template-only components, which the anchor
silently collapses.

## A9 · "Material = the Required module's Material reference" — HOLDS

**Assumption (stated).** `PARTICLES.json`'s `material` column is the required-module path, not the
material, so the pass re-reads `ParticleModuleRequired`'s Material reference.

**Test.** Checked what `PARTICLES.json` stores, and how every material pick was made:

```
PARTICLES.json emitter.material values: Batmobile_Explosion.ParticleModuleRequired (56),
  batmobileExhaust_burst.ParticleModuleRequired (52), … 1096 non-null, 337 null (stub emitters)
required-module Material picks: ref_class says Material 1018 | fell back to cand[0] 0
systems with >=1 material: 206
```

**Result.** **HOLDS.** The G1-6 column is literally `<System>.ParticleModuleRequired`, so the re-read is
justified rather than duplicated; all 1018 required modules resolved through a candidate whose
`ref_class` says Material, and the generator's fallback branch (`cand[0]` when no Material-classed ref
exists) never fired, so no material in the file came from a guess. 206/206 systems carry at least one.

## A10 · "Lifetime 203/206, the other 3 really have none" — HOLDS

**Test.** Listed the three rows without a lifetime and checked their emitters:

```
EMP_Burst_Charge | Playable_Batmobile{SF,MK2,Funhouse}_SF | emitters 4, with_levels 4, stubs 0,
  kinds {light: 4}, classes {ParticleSpriteEmitter: 4}
```

**Result.** **HOLDS.** They are one system in three packages, four LOD'd light emitters, no
`ParticleModuleLifetime` — genuinely no lifetime distribution in the cooked data, and the md prints
`-` rather than a default. (The fourth package's copy does carry one, which is why the count is 203
and not 206/204.)

## A11 · "Every system in exactly one group, `other` empty" — HOLDS

```
other | 0 | 0 | 0 | 0 | - | - | no system fell through the rules - every one of the 63 names matched a feature
group rows sum = 206 (asserted by --check)
```

**Result.** **HOLDS** — the partition is total. (Whether each assignment is the *right* feature is A2,
a different question; "no system ungrouped" should not be read as "no system mis-grouped".)

## A12 · Units and conventions — WEAK

**Assumption (silent).** `lifetime s`, `spawn /s`, `size`, and the colour triples are usable numbers.

**Test.** Searched the deliverable for any statement of unit or colour space:

```
$ grep -n 'cm\|unit\|metre\|meter' Research/BatmobileGrab/PARTICLES_FEATURES.md
(no output)
```

and looked at the magnitudes:

```
sonar    width  [0.2 0 0]..[400 50 0.1]
explosion size [0.1 0 0]..[25000 80 80]
colour   Start [0.0, 8.0, 1000.0]..[0.0, 8.0, 1000.0]   (EMP_Burst_Charge)
colour   Start [25.0, 12.0, 6.0]..[25.0, 12.0, 6.0]     (RiotSuppressor_BulletCasing)
```

**Result.** **WEAK.** Lifetime and spawn are labelled in seconds (a UE3 convention, not something the
decode proves), but size carries **no unit at all** and the colours carry **no colour space**. The
magnitudes are not self-explanatory: if size were Unreal units the 25000 would be 250 m, and every
colour triple above 1 means the values are not 0..1 RGBA. A T-17 consumer cannot convert any of this
to metres or to a shader colour without a convention the file does not state. This is the R4
"provenance" gap in its quietest form — the number is decoded, the unit is not.

## A13 · "`--check` proves the card's Done-when" — WEAK

**Assumption.** MODLOG: "**Verified:** `bmak_particle_features.py --check` → `OK …`", i.e. the green
gate stands for the card's Done.

**Test.** Read the check's assertions and ran them against the two failures found above. The check
verifies: 206 systems; every group in `GROUP_ORDER`; ≥8 groups; a non-empty reference set; external
refs grouped and noted; coverage arithmetic adds up; every MECHANICS wheel name is also an objects
ref; group rows sum to 206.

**Result.** **WEAK.** Nothing in it can fail on a *wrong* group (`NoTracer` in `tracer` passes), on a
*missing* reference (A3 passes), or on an extraction gap counted as a fact (A5 passes) — the gate
proves the table is complete and self-consistent, not that it is right. The card's Done-when is a
statement about coverage; the check tests a filtered coverage *and* its own arithmetic. It also pins
`systems != 206` as a hard failure, which is a reasonable "content changed" alarm but means the check
is an artefact diff, not a derivation of the card's clause.

## A14 · MODLOG's "44 from `WEAPONS.json`" — BROKEN (number)

**Assumption (stated).** *"49 referenced names — 44 from `WEAPONS.json` (G1-08/G1-09) plus 5 external
refs"*.

**Test.** Walked `WEAPONS.json` for `ParticleSystem` dicts and resolved their `target`/`path`; then the
same for the filter-passing `objects.jsonl` set:

```
WEAPONS.json ParticleSystem dicts: 337  (219 with a target/path; 118 carry neither)
distinct ParticleSystem names in WEAPONS.json: 30
filter-passing objects.jsonl names: 41
union: 49  ->  in the 206: 44, external: 5   (matches coverage 49 / 44 / 5)
WEAPONS-only names: 8 | objects-only: 19
```

**Result.** **BROKEN** as attributed: `WEAPONS.json` contributes 30 names (8 of them only there); the
44 is the *in-206* part of the 49-name union of both sources. The md's own coverage table is right;
only the MODLOG sentence is wrong. Worth fixing because it is the sentence a later session quotes when
it asks "where does the reference set come from" — and the answer it gives (WEAPONS.json) would hide
that 19 names come from the object scan and 118 `ParticleSystem` dicts in `WEAPONS.json` carry no
resolvable name at all (if any of those were real refs, they are invisible to this pass).

---

## What this challenge could not test

* **The component templates** for `WallScrape0/1`, `SpeedLines0`, `HeatSteam` (A4): the instance rows
  carry no template pointer, and the packages are compressed, so the system each one plays is
  **UNKNOWN** here. Proving "the feature is dead" or "the feature plays `X`" needs an archetype walk
  (`upk_read` on the component's archetype/default object), which is a card-sized job, not a probe.
* **Whether `PARTICLES.json`'s 337 nameless `ParticleSystem` dicts in `WEAPONS.json`** (A14) are
  duplicates of resolved refs or refs this walk cannot name — the walk has no path to name them.
* **Archetype-level colour/size** for the 4 systems with no `ParticleModuleSize` at all (A5): whether
  they inherit a default size is a class-default question, not in the grab.
* Everything else above was measured on the files on disk, read-only; no game was launched, nothing
  under `D:\Games` or the project outside this report was written, and nothing was committed.
