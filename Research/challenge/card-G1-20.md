# Assumption challenge — G1-20 · Skins and variants inventory

Challenger: Freebuff (did not write this card). Date: 2026-10-30. Read-only: nothing under
`GRAB_BACKLOG.md`, `MODLOG.md`, `Tools/`, `Working/`, the rest of `Research/` or the game install
was written; no game launched, no file in `D:\Games` touched, nothing installed, nothing
committed. This report is the only file written.

Inputs read: `GRAB_BACKLOG.md` §0.5 (R1–R14), the G1-20 card (line 537) and its §12 row (line
1288), `MODLOG.md` §"G1-20 · Skins and variants — done" (line 8660) and
§"G1-20 rework — intended change" (line 15745) / §"… rework — done" (line 15870),
`Research/BatmobileGrab/VARIANTS.md`, `Tools/scripts/grab_variants.py`, and the data it joins
(`objects.jsonl`, `MESHES.md`, `MESHES.json`, `LIGHTS.json`, `WEAPONS.md`) plus the packages
themselves.

## VERDICT

**The counts reproduce and the gate is honest; four of the six headline readings are wrong, and
the one thing the card was asked for — "sim/weapon value differences" — is answered "none" for a
car that retunes nine values.** 16 assumptions tested: **7 HOLD, 3 WEAK, 6 BROKEN.**

What holds: the variant set really is the four `Playable_Batmobile*` packages (a scan of all 46
`*Batmobile*.upk` for `RVehicleBatmobile` exports finds exactly those four, and the folder holds
exactly the 15 packages the note lists); the record counts 5,490 / 5,534 / 3,388 / 5,584; the
material counts 78 / 80 / 69 / 84 with extras 4/26/13 and missings 2/35/7; the texture counts
92 / 95 / 100 / 102 with 5/31/24 and 2/23/14; the light rigs 28 / 28 / 17 rows with
`MaterialType` on 18 / 18 / 0 (independently confirmed by `LIGHTS.json`, a different card's
artifact); the weapon objects 10 / 10 / 5 / 10 gadgets and 8 / 8 / 2 / 8 projectiles; the shared
weapon objects' values (17 objects in ≥2 packages, **0** differing scalar tags); and
`grab_variants.py --check` exits 0 with `VARIANTS.md` matching its own render.

What breaks:

1. **The Joker skin has 63 sockets, not 64.** The 64th `SkeletalMeshSocket` record,
   `BatmobileAttach`, is outered to `Batwing_Carrier.Batwing_Carrier` — a socket on the Batwing
   mesh, not on the car. `VARIANTS.md` counts records per package, so it reports "Joker | 64 | 64"
   and lists `BatmobileAttach` as a car socket the Joker gains. The card's own `In:` line already
   said `Batmobile_Jokerfied_Skin` **63**.
2. **"The Joker and Funhouse skins are the same export" is false**: both are 20,385,512 B but
   1,342 bytes differ in 754 runs (0x0 `29 04 00 00` vs `ac 03 00 00`), i.e. the same asset cooked
   twice with different export indices.
3. **"No skin changes handling" / "physics is shared" is answered from the wrong object.** The
   `SimulationModel` is tag-identical in all four, but the `JokersBatmobile` archetype itself
   retunes **nine** floats — `ImpactMaxDamageSpeed` 150→180, `ImpactMinDamageSpeed` 20→40,
   `ImpactStrafeMod` **2.25→0.8**, `BattleModeImpactMaxDamagePow` 0.5→0.666, `KillFlipTorque`
   −200→−400, `KillFlipTorqueDuration` 0.5→0.75, `ImpactRoadAssistSceneryDuration` 0→0.33,
   `ImpactRoadAssistEnemyDuration` 0.333→0.75, `WeaponGeneratorPowerTickUp` **2.0→0.0**.
4. **"which properties those 9 floats belong to is UNKNOWN" is false** — the SDK offset table names
   all nine, and this repo has already validated that table's origin on this class
   (`HealthRecoverRate` +8220, `ArmourLevels` +8108, `ArmourModeDamageReduction` +6424,
   `Pawn.Health` +1144 all match the serialised tag offsets).
5. **The §12 row says "Joker's tag diff is export indices, not values"** — the exact opposite of
   the artifact's own §6 table, which lists the nine values.
6. **"The same object, byte for byte" (sim)** is false as written: the four `SimulationModel`
   exports differ in 41 / 76 / 147 bytes of 2,328; only their 37 tags are identical.

---

## A1 · "The four variants = the four full vehicle packages"

**HOLDS**, and the discovery rule is wider than the note's own statement of it.

```
$ ls .../CookedPCConsole/Playable_Batmobile*.upk | wc -l
15          # 4 full + 11 _Std_*, exactly the 15 the note lists
$ python - (scan every *Batmobile*.upk, 46 files, for exports of class RVehicleBatmobile)
Playable_BatmobileFunhouse_SF.upk archetypes(RVehicleBatmobile)= 1   Vehicle.BatmobileFunhouse
Playable_BatmobileJoker_SF.upk   archetypes(RVehicleBatmobile)= 1   Vehicle.JokersBatmobile
Playable_BatmobileMK2_SF.upk     archetypes(RVehicleBatmobile)= 1   Vehicle.Batmobile_MK2
Playable_Batmobile_SF.upk        archetypes(RVehicleBatmobile)= 1   Vehicle.Batmobile
```

No fifth drivable variant exists in any package whose name contains "Batmobile". The residual (a
`RVehicleBatmobile` archetype inside a package *not* named Batmobile) is not excluded by either
test, but the four are confirmed as the complete set of *vehicle* archetypes and each is a
distinct skin.

## A2 · "Sockets 65 / 55 / 64 / 63"

**BROKEN for the Joker; the other three and every missing/extra list hold.**

The mesh carries its own socket list, so the claim can be checked at both levels:

```
mesh Sockets-array count vs SkeletalMeshSocket records
   V2        mesh_count=65  socket_records=65
   MK2       mesh_count=55  socket_records=55
   Joker     mesh_count=63  socket_records=64     ← one record is not on this mesh
   Funhouse  mesh_count=63  socket_records=63
sockets on other meshes: [('Playable_BatmobileJoker_SF', 'Batwing_Carrier.Batwing_Carrier', 'BatmobileAttach')]
```

Diffing the *mesh-level* sets (socket name at property offset 84) against V2:

```
Playable_Batmobile_SF            on-skin sockets=65
Playable_BatmobileMK2_SF         on-skin sockets=55
Playable_BatmobileJoker_SF       on-skin sockets=63
Playable_BatmobileFunhouse_SF    on-skin sockets=63

MK2      only-here(0)=[]   missing(10)=BrakeTrailL, BrakeTrailR, Dashboard_Light,
                           Headlight_Centre, LWheelLight, LWheelLight_bottom, LWheelLight_top,
                           RWheelLight, RWheelLight_bottom, RWheelLight_top
Joker    only-here(1)=[HydraSocket]                (note says: BatmobileAttach, HydraSocket)
         missing(3)=Dashboard_Light, Headlight_Centre, PassengerNoiseOrigin
Funhouse only-here(1)=[HydraSocket]
         missing(3)=Dashboard_Light, Headlight_Centre, PassengerNoiseOrigin
```

So the Joker gains exactly **one** socket, not two, and its total is 63. The card's `In:` line
(`MESHES.md` … `Batmobile_Jokerfied_Skin` 63) already had the right number; `VARIANTS.md`'s 64 is
the package count. (`MESHES.md` as it stands has no socket column at all — `grep -c socket
MESHES.md → 0` — so the card's citation of it for 55/63 is stale even though the numbers are
right.)

## A3 · "Materials 78 / 80 / 69 / 84, textures 92 / 95 / 100 / 102, every row closing"

**HOLDS.** Recounted from `objects.jsonl` by class, and the set differences re-derived:

```
materials {'V2': 78, 'MK2': 80, 'Joker': 69, 'Funhouse': 84}
   MK2       extra=4 missing=2
   Joker     extra=26 missing=35
   Funhouse  extra=13 missing=7
textures {'V2': 92, 'MK2': 95, 'Joker': 100, 'Funhouse': 102}
   MK2       extra=5 missing=2
   Joker     extra=31 missing=23
   Funhouse  extra=24 missing=14
```

Every figure, including the five rework corrections (35 not 38, 31/23, 24/14, nesting), reproduces.
The closure `count = reference − missing + extra` is arithmetic on the same sets, so it is a
consistency check, not independent evidence — but the counts themselves are right.

## A4 · "A skin is not a palette. V2 vs Joker: 61 materials and 54 textures differ"

**WEAK** — the numbers are package-level asset sets, and the sentence reads them as skin facts.

The skin binds 19 / 19 / 20 / 20 material **sections** (`MESHES.md` table, per-material LOD face
counts 0…18 for V2). The package carries 78 / 80 / 69 / 84 `Material` + `MaterialInstanceConstant`
records, which includes every FX material any object in that package needs. The Joker's "missing"
list shows the contamination directly: `EMP_BuildUp`, `EMP_Burst_V02_Stage_01…04`,
`DroneHacker_Beam`, `SeismicSonar_Smoke`, `fx_Winch_M_lit`, `Stagg_Battery_*` are absent because the
Joker car has **no EMP, sonar, winch or drone hacker** (A11), not because its skin lacks them.

The conclusion ("a tint would carry none of it") still follows — from the mesh, its 19/20 sections,
the sockets (A2) and the bones (220 vs 180) — but 61/54 is a package delta, not a skin delta, and
neither number changes if a variant is deleted from the car.

## A5 · "The Joker and Funhouse skins are the same export (20,385,512 B each)"

**BROKEN as worded.** Same size, same verts/faces/bones/materials, different bytes:

```
sizes 20385512 20385512
differing bytes: 1342 of 20385512 0.0066%
runs: 754  first 12: 0x4 0x20 0x34 0x40 0x54 0x154 0x17c 0x194 0x1c0 0x1d8 0x1e8 0x1f4
0x0  joker 09 00 94 00 29 04 00 00   funhouse 09 00 94 00 ac 03 00 00
```

The differences are export/import indices (`0x0429` vs `0x03ac`), the same phenomenon the note
correctly describes for the vehicle object. Content identical, export not — "the same export" is
the kind of identity claim R4 is meant to keep out; "the same mesh cooked into two packages" is
what the data shows.

## A6 · "`SimulationModel` identical in all four … the same object, byte for byte"

**WEAK.** The tag claim is true; byte identity is false.

```
V2        SimulationModel size=2328 tags=37 sha1=ba715c6abc951d75
MK2       SimulationModel size=2328 tags=37 sha1=68fae66662889a05
Joker     SimulationModel size=2328 tags=37 sha1=0b4e1147492219c7
Funhouse  SimulationModel size=2328 tags=37 sha1=257d7e894ea262cf
MK2       differing bytes=41 of 2328      Joker 147 of 2328      Funhouse 76 of 2328
tag signatures equal V2/Joker: True 37 37
```

So "0 differing tags" stands (and is what the argument needs), but the sentence next to it ("the
same object, byte for byte") does not — 41 bytes differ between the reference and MK2.

## A7 · "No skin changes handling" / "Physics is shared: a drop entry per skin needs no new sim tuning"

**BROKEN.** The sim object is shared; the car's impact/damage tuning is not.

Diffing every scalar tag (Int / Float / Byte / Bool) of the four `RVehicleBatmobile` archetypes
against V2, then naming each offset from `Working/vendor/BmSDK/*.g.cs`:

```
MK2       35 scalar tags, 0 differ from V2
Funhouse  35 scalar tags, 0 differ from V2
Joker     33 scalar tags, 9 differ from V2
   0x175c RVehicleBatmobileBase.ImpactRoadAssistSceneryDuration   V2=0.0    Joker=0.33
   0x1760 RVehicleBatmobileBase.ImpactRoadAssistEnemyDuration     V2=0.333  Joker=0.75
   0x1acc RVehicleBatmobileBase.ImpactMaxDamageSpeed              V2=150.0  Joker=180.0
   0x1ad0 RVehicleBatmobileBase.ImpactMinDamageSpeed              V2=20.0   Joker=40.0
   0x1ad4 RVehicleBatmobileBase.ImpactStrafeMod                   V2=2.25   Joker=0.8
   0x1aec RVehicleBatmobileBase.BattleModeImpactMaxDamagePow      V2=0.5    Joker=0.666
   0x1c18 RVehicleBatmobileBase.KillFlipTorque                    V2=-200.0 Joker=-400.0
   0x1c1c RVehicleBatmobileBase.KillFlipTorqueDuration            V2=0.5    Joker=0.75
   0x1eec RVehicleBatmobileBase.WeaponGeneratorPowerTickUp        V2=2.0    Joker=0.0
```

These are the very fields G1-14 decoded as the outgoing-ram chain: its note reads the band
"20→150 km/h" and "`ImpactStrafeMod` ×2.25" out of `CalculateAndStoreImpactDamage`, and the tags
here hold exactly `20.0`/`150.0` at 0x1AD0/0x1ACC and `2.25` at 0x1AD4. Two cards agreeing on the
same field identities is not a coincidence of offsets.

`WeaponGeneratorPowerTickUp = 0.0` on the Joker car also has a gameplay meaning G1-14 established
in its own section 5: the weapon generator is the car's shield, and here it never ticks up.

So the D-5 input "a drop entry per skin needs no sim tuning" is true of *physics* and false of
*damage/impact behaviour*, which the same archetype object serialises. MK2 and Funhouse really are
untouched (0 scalar diffs), which is a stronger statement than the note makes.

## A8 · "which properties those 9 floats belong to is UNKNOWN"

**BROKEN.** `VARIANTS.md` lists the nine offsets with "UNKNOWN" beside them; the SDK dump that the
same page already uses for `ArmourModeDamageReduction` etc. names every one (table in A7).

Three independent checks that the offset→name map is valid for this class:
1. `HealthRecoverRate` (+8220), `ArmourLevels` (+8108), `ArmourModeDamageReduction` (+6424):
   the SDK offsets equal the tag `offset` fields in `objects.jsonl`/the CDO.
2. G1-14's `CalculateAndStoreImpactDamage` trace reads the 20→150 band and ×2.25, matching
   `ImpactMinDamageSpeed`/`ImpactMaxDamageSpeed`/`ImpactStrafeMod` at 0x1AD0/0x1ACC/0x1AD4.
3. All four archetypes are the same class (`RVehicleBatmobile`), so a shared offset is the same
   member by construction — the note's caution ("a shared offset is not proof of a shared field")
   would only apply across different classes.

The note's UNKNOWN was the right instinct applied to the wrong case: it is right that
`JokersBatmobile` has a different *named* property set, and wrong that this prevents attribution.

## A9 · §12 row: "Joker's tag diff is export indices, not values"

**BROKEN.** The row contradicts the artifact it cites:

- §12: `… 10/10/5/10 gadgets and 8/8/2/8 projectile objects; Joker's tag diff is export indices,
  not values`
- `VARIANTS.md` §6: "Joker's 9 unnamed floats … listed because they move"
- this challenge: those 9 are values, and they are `Impact*`, `KillFlip*`,
  `WeaponGeneratorPowerTickUp` (A7).

A reader of the tracker gets the false summary of the whole card. (The MK2/Funhouse half of the
sentence is correct: 58/59 references differ only in index.)

## A10 · "28 / 28 / 17 light-rig rows with 18 / 18 / 0 `MaterialType`"

**HOLDS**, cross-checked against a second card's artifact rather than the generator's own code.

```
$ python - (LIGHTS.json entries)
Playable_BatmobileFunhouse_SF  entries=28 material_type=18
Playable_BatmobileJoker_SF     entries=17 material_type=0   last entry: Dashboard VEHLT_Interior
Playable_BatmobileMK2_SF       entries=28 material_type=18
Playable_Batmobile_SF          entries=28 material_type=18
```

and from the raw tag sizes (a row with `MaterialType` is larger): 18 rows ≥78 B of 28 in V2, none
≥78 B in Joker's 17. The Joker's last row being `Dashboard`/`VEHLT_Interior` where V2 has
`BootLight`/`VEHLT_BootLight` is confirmed verbatim.

## A11 · "10 / 10 / 5 / 10 gadgets and 8 / 8 / 2 / 8 projectile objects"

**HOLDS.** Recounted by class from `objects.jsonl`:

```
Playable_Batmobile_SF   RBasicProjectile 4, RBatmobileMissile 4, Booster/Cannon/EMP/EMPMissile/
                        HeavyCannon/MissileLauncher/Sonar/VehicleTracker/Winch 1 each
Joker                   RBatmobileCannon 2, RBasicProjectile 1, RBatmobileMissile 1, Booster 1,
                        HeavyCannon 1        → 5 gadgets, 2 projectiles
```

and the Joker genuinely has no EMP, EMP missile, sonar, tracker, winch or drone hacker. The
rework's corrections (8 projectiles not 4; 5 gadgets not 6; `ThreatComp` not a gadget) hold.

## A12 · "0 of 1065 field comparisons differ" / "the four packages carry the same weapon values"

**HOLDS** for the shared weapon objects, and the note's handling of WEAPONS.md's two totals is the
right kind of honesty.

```
weapon objects present in >1 package: 17
scalar/vector tag differences among shared weapon objects: 0
```

Both sentences really are in `WEAPONS.md` (`grep`: line 3 "0 of 332 fields compared", line 94
"0 of 1065 field comparisons differ"), so the UNKNOWN about which counts fields is accurate rather
than evasive. The limit: this holds for *weapon objects*; the vehicle object's own values differ
(A7), so the sentence must not be read as "no values differ across the four packages".

## A13 · The 11 `_Std_*` packages: "4 records each … that material is the upgrade-stage skin, not a vehicle"

**BROKEN as an omission** — the sentence is true and the data behind it is appearance data the
card's own scope needs.

```
Playable_Batmobile_Std_1_SF  RAddContentBatmobileMesh  playable_batmobile_std
      DamageChapter StructProperty      0.10  0.5
Playable_Batmobile_Std_2_SF  …  DamageChapter      0.12  0.60
Playable_Batmobile_Std_3_SF  …  DamageChapter      0.18
Playable_Batmobile_Std_4_SF  …  DamageChapter      0.25
Playable_Batmobile_Std_5_SF  …  DamageChapter      0.30
Playable_Batmobile_Std_6_SF  …  DamageChapter      0.45 + MaterialOverrides
      Material                    Batmobile_Stage6
      MaterialInstanceConstant    Batmobile_V3_Mainbody_Stage6_MIC
      MaterialInstanceConstant    Batmobile_V3_Weaponry_Stage6_MIC
      MaterialInstanceConstant    Batmobile_V3_WheelArchs_Stage6_MIC
Playable_BatmobileMK2_Std_1_SF … DamageChapter      0.55  1.45
```

That is a six-step damage-appearance ladder (0.10 → 0.45) plus a stage-6 body full-material
override set, in packages the note dismisses in one line. The card is `Skins and variants
inventory` serving `APP-8`, and D-5 is about putting skins in the drop; a JC3 appearance build has
to reproduce or deliberately drop the vanilla damage stages and the stage-6 override, and nothing
in `VARIANTS.md` records them. The note's own §8.1 also leans on the `*_Damage_ChapterMask` decals
while leaving the mechanism that consumes them uninventoried.

The structural reason is in the generator: `_Std_*` packages are read only for a record count
(there is no per-variant diff path for them), so `--check` cannot see this.

## A14 · Record counts and the archetype table

**HOLDS.**

```
Playable_Batmobile_SF          5,490   Playable_BatmobileMK2_SF       5,534
Playable_BatmobileJoker_SF     3,388   Playable_BatmobileFunhouse_SF  5,584
11 _Std_* packages: 4 records each, except Playable_Batmobile_Std_6_SF = 92
```

and the `outer` archetype names (`Batmobile_Archetypes.Vehicle`,
`Batmobile_Mk2_Archetypes.Vehicle`, `Batmobile_Joker_Archetypes.Vehicle`,
`Batmobile_Funhouse_Archetypes.Vehicle`) match the records.

## A15 · "sim/weapon value differences" (card `Do` 4) and "D-5 can be answered" (card `Done`)

**WEAK.** The card asks for *value* differences; the note answers "sim: none" and "weapon objects:
none" and never asks the archetype object, which is the only place values differ (A7). D-5 can be
answered from the page — but the answer it gives ("physics is shared", "the same weapon values")
is silent on the nine retuned values, so a build that copies them would be inventing them and a
build that ignores them would be dropping BmAK behaviour the record already knows.

## A16 · The page is generated and the gate is green

**HOLDS.** `python Tools/scripts/grab_variants.py --check` →

```
OK: 4 variants, 5,490 / 5,534 / 3,388 / 5,584 records; sockets 65/55/64/63; materials 78/80/69/84;
    textures 92/95/100/102; skin exports 20,151,210/20,034,142/20,385,512/20,385,512
OK: sim 0 differing tags in all four; rigs 28/28/17 rows, MaterialType 18/18; gadgets 10/10/5/10;
    tag diffs vs V2 86/77/87
OK: VARIANTS.md matches the re-derived render (340 lines)
EXIT=0
```

Everything above is consistent with itself — which is exactly the failure mode: the gate re-derives
the same per-package counters, so a scope error (package-level sockets, package-level material
sets, the archetype object never diffed) passes every time.

## What later cards should quote instead

| item | note says | on disk |
|---|---|---|
| Joker sockets | 64, adds `BatmobileAttach` + `HydraSocket` | **63** on the skin, adds `HydraSocket` only; `BatmobileAttach` is on `Batwing_Carrier` |
| Joker vs Funhouse skin | "the same export" | same mesh, **not** the same export: 1,342 bytes differ in 754 runs |
| `SimulationModel` | "the same object, byte for byte" | 37 identical tags; 41 / 76 / 147 differing bytes (MK2 / Funhouse / Joker) |
| handling / tuning | "No skin changes handling", "physics is shared" | sim identical; Joker retunes 9 vehicle values (`ImpactStrafeMod` 2.25→0.8, `ImpactMaxDamageSpeed` 150→180, `WeaponGeneratorPowerTickUp` 2→0, …) |
| the 9 unnamed floats | "which properties … is UNKNOWN" | `ImpactRoadAssistSceneryDuration`, `ImpactRoadAssistEnemyDuration`, `ImpactMaxDamageSpeed`, `ImpactMinDamageSpeed`, `ImpactStrafeMod`, `BattleModeImpactMaxDamagePow`, `KillFlipTorque`, `KillFlipTorqueDuration`, `WeaponGeneratorPowerTickUp` |
| `_Std_*` packages | "the upgrade-stage skin, not a vehicle" | six `DamageChapter` steps 0.10→0.45 (+0.55/1.45 on MK2) and a stage-6 `MaterialOverrides` set with 3 MICs and `Batmobile_Stage6` |

## Appendix · commands used

```bash
# variant set: 15 Playable_Batmobile*.upk in the folder; scan the 46 *Batmobile*.upk for
# exports whose class is RVehicleBatmobile -> 4, one per full package

# sockets at mesh level: SkeletalMesh tag `Sockets` count, and SkeletalMeshSocket records
# grouped by `outer` (the skin mesh vs Batwing_Carrier); socket name = tag at offset 84

# scalars of the four archetypes, named from the SDK offset table
python - <<'PY'   # parse "/// <T>Property: <name>" + "Ptr + N" from Working/vendor/BmSDK/*.g.cs
# then diff {offset: value} for RVehicleBatmobile tags of type_id 2/3/4 against V2
PY

# byte identity of two exports
python - <<'PY'
import sys; sys.path.insert(0,'Tools/scripts'); import upk_read as U
D=r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole"
def mesh(p,n):
    pkg=U.Package(D+"\\"+p+".upk")
    return next(pkg.data(i) for i in range(1,len(pkg.exports)+1)
                if pkg.exports[i-1]["name"]==n and pkg.object_class(i)=="SkeletalMesh")
a=mesh("Playable_BatmobileJoker_SF","Batmobile_Jokerfied_Skin")
b=mesh("Playable_BatmobileFunhouse_SF","Batmobile_Jokerfied_Skin")
print(sum(1 for x,y in zip(a,b) if x!=y), "of", len(a))
PY

python Tools/scripts/grab_variants.py --check       # EXIT=0, 340 lines
```
