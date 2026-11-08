# T-WP4d - the tracker and the Immobiliser, corrected

**STATUS: done.** Both review points are confirmed against the cooked packages and corrected in new
files. `t_wp4c.py` and every T-WP4c output are untouched.

Summary:

- **C1 (wrong label).** The tracker's `bInstantFire = true (class default)` is **UNKNOWN**: none of the
  three `Vehicle_Tracker` records serializes offset 2464, and no class-default object carries it. The
  `true` belongs to `Batmobile_EMP_Missile_Launcher`. Root cause found: `t_wp4c.py`'s `av()` fell back
  from an archetype's own rows to a class-wide row dict that is first-wins across all archetypes, so the
  EMP launcher's row stood in for the tracker's.
- **C2/C3 (wrong attribution).** Both payload pointers on `Batmobile_EMP_Missile_Launcher` (offsets 2492
  and 2428) resolve to **`Batmobile_EMPMissile_Projectile_ForCars`** (export 5116). The impact sound
  `Ww_VFX_Tank_Explosion.Play_Batmobile_Immobiliser_Impact` and `Projectile.Damage 60.0` sit on
  `Batmobile_EMPMissile_Projectile` (export 16), which **no export in any of the four packages
  references**. The fired archetype is reference-only: 10 tags, **0 scalars, 0 AkEvents**. Its damage and
  impact sound are therefore **UNKNOWN**, not 60.0 and not the Immobiliser event.
- **C4** the merged `§2.3` table is split into one table per archetype; **C5** the rotator degrees are
  printed with the rounding (`5461 -> 29.9982 deg`, not "30.0"), and the up/down sign is not asserted.
- One defect of my own was caught and fixed before the final write: a raw `offset == 2464` scan matched
  four unrelated classes (a Cannon muzzle flash, a Winch sound, a Drone-Hacker loop), so the census is
  now filtered to the class lineage that actually declares the field. Disclosed in §"What I had to fix
  in my own first version" below.

## Files written

| file | what |
|---|---|
| `Tools/scripts/t_wp4d.py` | new generator, `--write` / `--check`; re-reads the packages every run |
| `Working/Translation/T_WP4D_TRACKER_EMP.md` | 29,956 chars - the corrected document |
| `Working/Translation/T_WP4D_TRACKER_EMP.json` | 35,603 chars - the same data |
| `tmp/freebuff/scratch/wp4d_check.py` | probe 1 (launcher pointers, tracker, both projectiles) |
| `tmp/freebuff/scratch/wp4d_probe2.py` | probe 2 (class defaults, 2464 carriers, reverse refs) |
| `tmp/freebuff/reports/T-WP4d.md` | this report |

Not touched: `Tools/scripts/t_wp4c.py`, `Working/Translation/T_WP4C_TRACKER_EMP.md/.json`,
`Research/BatmobileGrab/**`, the game installs.

## What was re-checked, and against what

Every value was read from the bytes with `Tools/scripts/upk_read.py` (`Package`, `export_summary`), in
`E:/Games/Batman - Arkham Knight/BmGame/CookedPCConsole`: `Playable_Batmobile_SF.upk` (5,490 exports),
`Playable_BatmobileMK2_SF.upk` (5,534), `Playable_BatmobileFunhouse_SF.upk` (5,584),
`Playable_BatmobileJoker_SF.upk` (3,388), `BmGame.upk` (class defaults). Field names are cross-checked
against `Working/vendor/BmSDK/*.g.cs` at run time; the document prints the witness for all 17 offsets and
none is `(none)`. Read-only: no launch, no inject, no attach (INSTRUCTIONS.md §3).

## The two review points, as the bytes settle them

### Point 1 - the tracker's `bInstantFire`

```
Playable_Batmobile_SF.upk  Batmobile_EMP_Missile_Launcher  class=RBatmobileEMPMissile  tags=21
   @2464 0x09A0 BoolProperty (offset-only) = True
Playable_Batmobile_SF.upk  Vehicle_Tracker  class=RBatmobileVehicleTracker  tags=7
   tags at 360, 792, 2176, 2200, 2428, 2436, 2452  -- no 2464
```

`bInstantFire` carriers, filtered to the `RPursuitModeMissileLauncher` chain (the classes that declare the
field at 2464): Batmobile 1 (`Batmobile_EMP_Missile_Launcher`), MK2 1, Funhouse 1, Joker 0. Tick
`Vehicle_Tracker`: **0**.

Class-default objects in `BmGame.upk`:

| CDO | export | tags | offsets | 2464? |
|---|---:|---:|---|---|
| `Default__RPursuitModeMissileLauncher` | 46742 | 1 | [792] | **no** |
| `Default__RBatmobileVehicleTracker` | 47800 | 5 | [785, 792, 1204, 2444, 2448] | **no** |
| `Default__RBatmobileMissile` | 47283 | 15 | [92, 124, 180, 668, 672, 704, 816, 840, 848, 1040, 1048, 1060, 1064, 1080, 1084] | **no** |

So no decoded record carries the tracker's value: **UNKNOWN**. World knowledge that "RVehicleWeapon
weapons are instant-fire" is exactly what the rules forbid using here.

### Point 2 - which projectile, and what it carries

```
Batmobile_EMP_Missile_Launcher (export 5114):
   @2492 -> Projectiles.Batmobile_EMPMissile_Projectile_ForCars
   @2428 -> Projectiles.Batmobile_EMPMissile_Projectile_ForCars
reverse scan: refs to _ForCars = 2 (both from export 5114); refs to Batmobile_EMPMissile_Projectile = 0
```

| quantity | fired `_ForCars` (5116) | sibling `Batmobile_EMPMissile_Projectile` (16) |
|---|---|---|
| `Projectile.Damage` @728 | absent | 60.0 |
| `Projectile.DamageRadius` @732 | absent | 0.0 |
| `Projectile.MyDamageType` @712 | absent | `Core.RDmgType_BatmobileCannon` |
| `RBatmobileMissile.ExlposionSound` @968 | absent | `Play_Batmobile_Immobiliser_Impact` |
| `RBatmobileMissile.ExplosionTemplate` @960 | `Rocket.Batmobil_Rocket_Explosion_Small` | `Rocket.Batmobil_Rocket_Explosion` |
| tags / scalars / AkEvents | 10 / 0 / 0 | 20 / 4 / 3 |

The fired archetype's only audio member is an `RAkAudible` **component**
(`..._ForCars.DefaultAkAudible_`, offset 124) - not an `AkEvent` - so which event it plays is not in the
packages. Class defaults (`Default__RBatmobileMissile`, `Default__RProjectile`,
`Default__RBasicProjectile`) serialize nothing at 712/728/732/968. Damage and impact sound of the fired
missile: **UNKNOWN**, with the route named in the document (engine/native projectile defaults, or a
runtime sample).

## What I had to fix in my own first version

My first `--write` printed a census like `4 carriers: Drone_Hacker, Batmobile_Cannon_V2,
Batmobile_EMP_Missile_Launcher, Batmobile_Winch`. That is a real trap in this data: **offset 2464 is
class-relative**, and three unrelated classes have a different field at that number. Two bugs, both
caught by reading my own output before trusting it:

1. the scan was not filtered to the class lineage that declares the field - fixed by walking the SDK
   superclass chain (`RBatmobileEMPMissile -> RPursuitModeMissileLauncher`,
   `RBatmobileVehicleTracker -> RPursuitModeMissileLauncher`; the Cannon/Winch/Drone-Hacker classes are
   outside it) and printing the collisions separately;
2. the superclass regex missed the real declaration (`public partial class X : BmSDK.BmGame.Y, ...`), so
   the lineage was empty and the first fix would have printed `0 carriers` - i.e. the opposite error.
   `Projectile.MyDamageType` also showed `(none)` until `ClassProperty:` was added to the field regex.

Both are visible in the transcript below, and the final document shows the corrected tables plus the
off-chain collisions by name, so a reader can check the filter rather than trust it.

## Commands and verbatim output

### 1. Probe 1 - launcher pointers, tracker, both projectiles

```
$ cd E:/Modding/JC3-Batmobile && PYTHONIOENCODING=utf-8 uv run python tmp/freebuff/scratch/wp4d_check.py
root E:/Games\Batman - Arkham Knight\BmGame\CookedPCConsole
====================================================================================================
Playable_Batmobile_SF.upk 5490 exports
 launcher:
  Batmobile_EMP_Missile_Launcher: RBatmobileEMPMissile size=223 tags=21 stop=eof
     @2492 ObjectNCRProperty (offset-only)              -> Projectiles.Batmobile_EMPMissile_Projectile_ForCars (RBatmobileMissile)
     @2508 ObjectNCRProperty (offset-only)              -> Ww_CHR_BatmanAlerts.Play_HUD_fail (AkEvent)
     @2560 FloatProperty    (offset-only)              = 2.0
     @2564 FloatProperty    (offset-only)              = 1.0
     @2640 FloatProperty    (offset-only)              = 600.0
     @2644 FloatProperty    (offset-only)              = 800.0
     @2428 ObjectNCRProperty (offset-only)              -> Projectiles.Batmobile_EMPMissile_Projectile_ForCars (RBatmobileMissile)
     @2436 NameProperty     (offset-only)              = 'BattleModeSpotLight'
     @2452 RotatorProperty  (offset-only)              = [-3640, 0, 0]
     @2464 BoolProperty     (offset-only)              = True
 projectile (unfired sibling):
  Batmobile_EMPMissile_Projectile: RBatmobileMissile size=167 tags=20 stop=eof
     @ 960 ObjectNCRProperty (offset-only)              -> Rocket.Batmobil_Rocket_Explosion (ParticleSystem)
     @ 968 ObjectNCRProperty (offset-only)              -> Ww_VFX_Tank_Explosion.Play_Batmobile_Immobiliser_Impact (AkEvent)
     @1064 FloatProperty    (offset-only)              = 40000.0
     @ 808 ObjectNCRProperty (offset-only)              -> Damage_States.FireTrail_APC (ParticleSystem)
     @ 672 FloatProperty    (offset-only)              = 7500.0
     @ 712 ObjectNCRProperty (offset-only)              -> Core.RDmgType_BatmobileCannon (Class)
     @ 728 FloatProperty    (offset-only)              = 60.0
     @ 732 FloatProperty    (offset-only)              = 0.0
 projectile _ForCars:
  Batmobile_EMPMissile_Projectile_ForCars: RBatmobileMissile size=83 tags=10 stop=eof
     @ 960 ObjectNCRProperty (offset-only)              -> Rocket.Batmobil_Rocket_Explosion_Small (ParticleSystem)
     @1040 ObjectNCRProperty (offset-only)              -> Batmobile_EMPMissile_Projectile_ForCars.RocketTrail (ParticleSystemComponent)
     @ 808 ObjectNCRProperty (offset-only)              -> Damage_States.FireTrail_Car (ParticleSystem)
     @ 816 ObjectNCRProperty (offset-only)              -> Batmobile_EMPMissile_Projectile_ForCars.RB_RadialImpulseComponent (RB_RadialImpulseComponent)
     @ 704 ObjectNCRProperty (offset-only)              -> Batmobile_EMPMissile_Projectile_ForCars.CollisionCylinder (CylinderComponent)
     @ 124 ObjectNCRProperty (offset-only)              -> Batmobile_EMPMissile_Projectile_ForCars.DefaultAkAudible_ (RAkAudible)
 tracker:
  Vehicle_Tracker: RBatmobileVehicleTracker size=75 tags=7 stop=eof
     @2428 ObjectNCRProperty (offset-only)              -> Projectiles.Batmobile_Tracker_Projectile (RBatmobileMissile)
     @2436 NameProperty     (offset-only)              = 'BattleModeSpotLight'
     @2452 RotatorProperty  (offset-only)              = [5461, 0, 0]
     @2176 ObjectNCRProperty (offset-only)              -> ww_chr_batmandisruptor.Play_BatSniperRifle_Vehicle_Tracking_Fire (AkEvent)
     @2200 ObjectNCRProperty (offset-only)              -> ww_chr_batmandisruptor.Play_BatSniperRifle_Vehicle_Tracking_Fire (AkEvent)
     @ 792 ObjectNCRProperty (offset-only)              -> Vehicle_Tracker.GadgetMesh (SkeletalMeshComponent)
     @ 360 NameProperty     (offset-only)              = 'RBatmobileVehicleTracker'
 projects tagged EMPMissile/Tracker:
       16 Batmobile_EMPMissile_Projectile
     5116 Batmobile_EMPMissile_Projectile_ForCars
     5121 Vehicle_Tracker
```

(Abridged only where it repeats the same three archetypes for MK2/Funhouse; the full run is the command
above. Output for those two packages is byte-identical in every field quoted here - the tool asserts that
by re-reading them.)

### 2. Probe 2 - class defaults, 2464 carriers, reverse references

```
$ cd E:/Modding/JC3-Batmobile && PYTHONIOENCODING=utf-8 uv run python tmp/freebuff/scratch/wp4d_probe2.py > tmp/freebuff/scratch/wp4d_probe2.out 2>&1; echo "EXIT=$?"; sed -n '1,80p' tmp/freebuff/scratch/wp4d_probe2.out
EXIT=0
root E:/Games\Batman - Arkham Knight\BmGame\CookedPCConsole
====================================================================================================
BmGame.upk default objects
  Default__RPursuitModeMissileLauncher: export 46742 class=RPursuitModeMissileLauncher size=10 tags=1 stop=eof
  Default__RBatmobileVehicleTracker: export 47800 class=RBatmobileVehicleTracker size=66 tags=5 stop=eof
  Default__RBatmobileMissile: export 47283 class=RBatmobileMissile size=154 tags=15 stop=eof
   @1064 0x0428 FloatProperty    (offset-only)                  = 15000.0
   @ 672 0x02A0 FloatProperty    (offset-only)                  = 10000.0
  Default__RBatmobileEMPMissile: export 46889 class=RBatmobileEMPMissile size=229 tags=25 stop=eof
  Default__RBasicProjectile: export 45069 class=RBasicProjectile size=122 tags=11 stop=eof
  Default__RProjectile: export 31486 class=RProjectile size=94 tags=9 stop=eof
  Default__Projectile: NOT FOUND in BmGame.upk
====================================================================================================
every export in the four vehicle packages that serializes offset 2464 (0x09A0) / a *InstantFire* tag
  Playable_Batmobile_SF.upk export 5114 Batmobile_EMP_Missile_Launcher:
   @2464 0x09A0 BoolProperty     (offset-only)                  = True
  Playable_Batmobile_SF.upk: 1 carrier tag(s)
  Playable_BatmobileMK2_SF.upk export 5165 Batmobile_EMP_Missile_Launcher:
   @2464 0x09A0 BoolProperty     (offset-only)                  = True
  Playable_BatmobileMK2_SF.upk: 1 carrier tag(s)
  Playable_BatmobileFunhouse_SF.upk export 5204 Batmobile_EMP_Missile_Launcher:
   @2464 0x09A0 BoolProperty     (offset-only)                  = True
  Playable_BatmobileFunhouse_SF.upk: 1 carrier tag(s)
  Playable_BatmobileJoker_SF.upk: 0 carrier tag(s)
====================================================================================================
Playable_Batmobile_SF.upk Batmobile_EMPMissile_Projectile: export 16 class=RBatmobileMissile size=167 tags=20 stop=eof
   @ 960 0x03C0 ObjectNCRProperty (offset-only)                  -> Rocket.Batmobil_Rocket_Explosion (ParticleSystem)
   @ 968 0x03C8 ObjectNCRProperty (offset-only)                  -> Ww_VFX_Tank_Explosion.Play_Batmobile_Immobiliser_Impact (AkEvent)
   @ 992 0x03E0 ObjectNCRProperty (offset-only)                  -> Engine.Play_Batmobile_ApRocket_Up (AkEvent)
   @1016 0x03F8 ObjectNCRProperty (offset-only)                  -> Engine.Play_Batmobile_ApRocket_Flight (AkEvent)
   @1040 0x0410 ObjectNCRProperty (offset-only)                  -> Batmobile_EMPMissile_Projectile.RocketTrail (ParticleSystemComponent)
   @1048 0x0418 ObjectNCRProperty (offset-only)                  -> Batmobile_EMPMissile_Projectile.Mesh0 (StaticMeshComponent)
   @1064 0x0428 FloatProperty    (offset-only)                  = 40000.0
   @ 840 0x0348 ObjectNCRProperty (offset-only)                  -> Batmobile_EMPMissile_Projectile.Mesh0 (StaticMeshComponent)
   @ 848 0x0350 ObjectNCRProperty (offset-only)                  -> Batmobile_EMPMissile_Projectile.RocketTrail (ParticleSystemComponent)
   @ 808 0x0328 ObjectNCRProperty (offset-only)                  -> Damage_States.FireTrail_APC (ParticleSystem)
   @ 816 0x0330 ObjectNCRProperty (offset-only)                  -> Batmobile_EMPMissile_Projectile.RB_RadialImpulseComponent (RB_RadialImpulseComponent)
   @ 824 0x0338 BoolProperty     (offset-only)                  = True
   @ 672 0x02A0 FloatProperty    (offset-only)                  = 7500.0
   @ 704 0x02C0 ObjectNCRProperty (offset-only)                  -> Batmobile_EMPMissile_Projectile.CollisionCylinder (CylinderComponent)
   @ 712 0x02C8 ObjectNCRProperty (offset-only)                  -> Core.RDmgType_BatmobileCannon (Class)
   @ 728 0x02D8 FloatProperty    (offset-only)                  = 60.0
   @ 732 0x02DC FloatProperty    (offset-only)                  = 0.0
   @ 124 0x007C ObjectNCRProperty (offset-only)                  -> Batmobile_EMPMissile_Projectile.DefaultAkAudible_ (RAkAudible)
   @ 180 0x00B4 ObjectNCRProperty (offset-only)                  -> Batmobile_EMPMissile_Projectile.CollisionCylinder (CylinderComponent)
   @ 360 0x0168 NameProperty     (offset-only)                  = 'RBatmobileMissile'

Playable_Batmobile_SF.upk Batmobile_EMPMissile_Projectile_ForCars: export 5116 class=RBatmobileMissile size=83 tags=10 stop=eof
   @ 960 0x03C0 ObjectNCRProperty (offset-only)                  -> Rocket.Batmobil_Rocket_Explosion_Small (ParticleSystem)
   @1040 0x0410 ObjectNCRProperty (offset-only)                  -> Batmobile_EMPMissile_Projectile_ForCars.RocketTrail (ParticleSystemComponent)
   @1048 0x0418 ObjectNCRProperty (offset-only)                  -> Batmobile_EMPMissile_Projectile_ForCars.Mesh0 (StaticMeshComponent)
   @ 840 0x0348 ObjectNCRProperty (offset-only)                  -> Batmobile_EMPMissile_Projectile_ForCars.Mesh0 (StaticMeshComponent)
   @ 848 0x0350 ObjectNCRProperty (offset-only)                  -> Batmobile_EMPMissile_Projectile_ForCars.RocketTrail (ParticleSystemComponent)
   @ 808 0x0328 ObjectNCRProperty (offset-only)                  -> Damage_States.FireTrail_Car (ParticleSystem)
   @ 816 0x0330 ObjectNCRProperty (offset-only)                  -> Batmobile_EMPMissile_Projectile_ForCars.RB_RadialImpulseComponent (RB_RadialImpulseComponent)
   @ 704 0x02C0 ObjectNCRProperty (offset-only)                  -> Batmobile_EMPMissile_Projectile_ForCars.CollisionCylinder (CylinderComponent)
   @ 124 0x007C ObjectNCRProperty (offset-only)                  -> Batmobile_EMPMissile_Projectile_ForCars.DefaultAkAudible_ (RAkAudible)
   @ 180 0x00B4 ObjectNCRProperty (offset-only)                  -> Batmobile_EMPMissile_Projectile_ForCars.CollisionCylinder (CylinderComponent)
====================================================================================================
export indices: {'Batmobile_EMPMissile_Projectile': 16, 'Batmobile_EMPMissile_Projectile_ForCars': 5116}
  export 5114 Batmobile_EMP_Missile_Launcher @2492 (offset-only) -> Projectiles.Batmobile_EMPMissile_Projectile_ForCars
  export 5114 Batmobile_EMP_Missile_Launcher @2428 (offset-only) -> Projectiles.Batmobile_EMPMissile_Projectile_ForCars
```

### 3. The SDK facts the lineage filter and the witnesses need

```
$ cd E:/Modding/JC3-Batmobile && grep -n "partial class RBatmobileEMPMissile\|partial class RBatmobileVehicleTracker\|partial class RBatmobileMissile\b\|partial class RPursuitModeMissileLauncher" Working/vendor/BmSDK/*.g.cs
Working/vendor/BmSDK/RBatmobileEMPMissile.g.cs:11:public partial class RBatmobileEMPMissile : BmSDK.BmGame.RPursuitModeMissileLauncher, BmSDK.IGameObject
Working/vendor/BmSDK/RBatmobileVehicleTracker.g.cs:11:public partial class RBatmobileVehicleTracker : BmSDK.BmGame.RPursuitModeMissileLauncher, BmSDK.IGameObject
Working/vendor/BmSDK/RBatmobileMissile.g.cs:11:public partial class RBatmobileMissile : BmSDK.BmGame.RBasicProjectile, BmSDK.IGameObject
Working/vendor/BmSDK/RPursuitModeMissileLauncher.g.cs:11:public partial class RPursuitModeMissileLauncher : BmSDK.BmGame.RVehicleWeapon, BmSDK.IGameObject
$ grep -n "MyDamageType" Working/vendor/BmSDK/Projectile.g.cs
462:    /// ClassProperty: MyDamageType
464:    public unsafe BmSDK.Class MyDamageType
       get { ... ToManaged<BmSDK.Class>(Ptr + 712); }
```

### 4. First `--write` (the version I rejected)

```
$ cd E:/Modding/JC3-Batmobile && PYTHONIOENCODING=utf-8 uv run python Tools/scripts/t_wp4d.py --write
wrote Working/Translation/T_WP4D_TRACKER_EMP.md (27855 chars)
wrote Working/Translation/T_WP4D_TRACKER_EMP.json (34702 chars)
```

Reading that output showed the census claiming four 2464 carriers including `Drone_Hacker`,
`Batmobile_Cannon_V2` and `Batmobile_Winch` - the class-relative-offset bug. Fixed as described above;
the counts in that file were never reported as a result.

### 5. Final write and check

```
$ cd E:/Modding/JC3-Batmobile && PYTHONIOENCODING=utf-8 uv run python Tools/scripts/t_wp4d.py --write && PYTHONIOENCODING=utf-8 uv run python Tools/scripts/t_wp4d.py --check; echo "CHECK_EXIT=$?"
wrote Working/Translation/T_WP4D_TRACKER_EMP.md (29956 chars)
wrote Working/Translation/T_WP4D_TRACKER_EMP.json (35603 chars)
OK Working/Translation/T_WP4D_TRACKER_EMP.md (29956 chars)
OK Working/Translation/T_WP4D_TRACKER_EMP.json (35603 chars)
CHECK PASS
CHECK_EXIT=0
```

### 6. The carried appendix really is T-WP4c verbatim

```
$ cd E:/Modding/JC3-Batmobile && uv run python - <<'PY'
import hashlib, re
md = open("Working/Translation/T_WP4D_TRACKER_EMP.md", encoding="utf-8").read()
src = open("Working/Translation/T_WP4C_TRACKER_EMP.md", encoding="utf-8").read()
carried = re.findall(r"<!-- carried: (.*?) \| (\d+) chars \| sha256 ([0-9a-f]{64}) -->\n\n(.*?)(?=\n\n<!-- carried:|\n\n## 7\.)", md, re.S)
ok = True
for head, n, sh, body in carried:
    body = body.rstrip("\n")
    h = hashlib.sha256(body.encode()).hexdigest()
    inside = body in src
    print(f"{'OK ' if (h == sh and inside) else 'BAD'} {head}: {len(body)} chars sha {h[:12]} in-T-WP4c={inside} sha-match={h==sh}")
    ok &= (h == sh and inside)
print("CARRIED_VERBATIM", "PASS" if ok else "FAIL")
PY
OK  3. The booster mesh: 1092 chars sha 1fec595f47a9 in-T-WP4c=True sha-match=True
OK  4. The JC3 house for tracker + missile + mesh: 3024 chars sha 65493b6725e1 in-T-WP4c=True sha-match=True
OK  6. COMPROMISES (unapproved - the operator approves through Claude): 1740 chars sha a72bbd03398a in-T-WP4c=True sha-match=True
OK  7. Reopened closures: 1136 chars sha e631f4de69fd in-T-WP4c=True sha-match=True
OK  8. Checks: 356 chars sha 7251279dbdb9 in-T-WP4c=True sha-match=True
CARRIED_VERBATIM PASS
```

## UNKNOWNs, each with what was tried

1. **The fired missile's `Projectile.Damage` / `DamageRadius` / `MyDamageType`.** Tried: all 10 tags of
   `Batmobile_EMPMissile_Projectile_ForCars` in all four vehicle packages (all object references, 0
   scalars); `Default__RBatmobileMissile` (15 tags, none at 712/728/732), `Default__RProjectile` (9),
   `Default__RBasicProjectile` (11). Nothing in the packages supplies it. Where it would be found: the
   engine-side `RBatmobileMissile` CDO outside the cooked packages, or a runtime sample of the missile's
   hit.
2. **The fired missile's impact sound.** Same search; the fired archetype's `RAkAudible` component at offset 124
   has no serialized event, and the only `Immobiliser` event in the weapon data is on the orphan
   sibling. Not guessed as "the sibling's sound, therefore the same".
3. **The tracker's `bInstantFire`.** Tried: the `Vehicle_Tracker` record in Batmobile/MK2/Funhouse/Joker,
   every 2464 carrier in those packages (lineage-filtered and raw), and the three class-default objects.
   The value is not in the bytes.
4. **`AutoTargetAngle` / `Range` for the tracker** - carried over from T-WP4c as UNKNOWN; this card did
   not re-open them (nothing in the packages changed for them).
5. **Which way +pitch tilts the tracker's socket.** The unit rule is decoded (65,536 per turn), the sign
   is stated nowhere, so the document prints units and degrees and no direction.
6. **The disable's duration and look** - unchanged from T-WP4c §2.4: no member on the missile class or
   either projectile.

## COMPROMISES

None added. C1-C5 are accuracy restorations; the three compromises T-WP4c lists (C1 tag half, C2
disable, C3 booster mesh) are carried unchanged in §6 and still need the operator's approval.

## Notes for whoever reads T-WP4d next

- `Tools/scripts/t_wp4c.py` remains runnable and still produces the old (wrong) labels. It is not
  patched, per the brief. If the operator wants one document instead of two, the minimal patch is its
  `av()` fallback: drop the `allrows` fallback so a value is only reported when the archetype's own
  section has the row. That is a one-line change plus a `--write`, and it would change exactly C1.
- The `T_WP4D` JSON carries the same numbers as the MD plus the raw tag lists, so a reviewer can
  re-derive without parsing prose.
