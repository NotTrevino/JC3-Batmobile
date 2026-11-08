# The Immobiliser, launch side: payload and pointers (build plan)

**STATUS: plan complete, one engineering blocker named.** The launcher's pointers need **no edit** — both
already resolve to `Batmobile_EMPMissile_Projectile_ForCars` in all three Batmobile packages (measured
today, 6/6 PASS). What is missing is the **payload on that archetype**: the damage, damage type and
Immobiliser impact sound sit on `Batmobile_EMPMissile_Projectile` (export 16), which **0 exports
reference**. The build step is therefore "add four tags to the fired archetype", not "move a pointer".

Evidence: `tmp/freebuff/reports/T-WP4d.md` (C1-C5), `Working/Translation/T_WP4D_TRACKER_EMP.{md,json}`,
`Working/Translation/T_WP4C_TRACKER_EMP.md` §2.3-2.4, `Working/vendor/BmSDK/*.g.cs`,
`Research/JC3Grab/EMP.md`, `Research/JC3Grab/FORCEPULSE.md`, `Working/Weapons/manifest.json`, and the
two runs quoted below. The game install was read only: nothing launched, injected or written.

## 0. What was measured today

```
$ cd E:/Modding/JC3-Batmobile && PYTHONIOENCODING=utf-8 python Tools/scripts/wp4_emp_payload_check.py
root E:/Games\Batman - Arkham Knight\BmGame\CookedPCConsole

Playable_Batmobile_SF.upk  exports=5490  launcher=5114 fired=5116 orphan=16
  PASS  launcher @2428 -> Batmobile_EMPMissile_Projectile_ForCars: Projectiles.Batmobile_EMPMissile_Projectile_ForCars
  PASS  launcher @2492 -> Batmobile_EMPMissile_Projectile_ForCars: Projectiles.Batmobile_EMPMissile_Projectile_ForCars
  FAIL  fired @728 Damage == 60.0: absent
  FAIL  fired @732 DamageRadius == 0.0: absent
  FAIL  fired @712 MyDamageType == Core.RDmgType_BatmobileCannon: (none)
  FAIL  fired @968 impact sound == Immobiliser: (none)
  fired tags=10 size=83  launcher tags=21  @2464 bInstantFire=True  @2452 rotator=[-3640, 0, 0]
   (MK2: launcher=5165 fired=5167 orphan=16 — identical verdicts)
   (Funhouse: launcher=5204 fired=5206 orphan=16 — identical verdicts)

$ ... --reverse
  reverse refs (walked 5490 exports in 0.3s): Batmobile_EMPMissile_Projectile=0  Batmobile_EMPMissile_Projectile_ForCars=2
  PASS  orphan Batmobile_EMPMissile_Projectile still has 0 incoming refs: 0
CHECK FAIL (12)   EXIT=1
```

Baseline: **7 assertions pass, 12 fail** (4 payload assertions × 3 packages). The failures are the work.

| package | bytes (sha256 prefix) | launcher | fired | orphan |
|---|---|---:|---:|---:|
| `Playable_Batmobile_SF.upk` | `f8c1e41047989a0d023a1ed2` | 5114 | 5116 | 16 |
| `Playable_BatmobileMK2_SF.upk` | `620a6e18dd85adece8782fbf` | 5165 | 5167 | 16 |
| `Playable_BatmobileFunhouse_SF.upk` | `a3b784fa021ada02804e3a4d` | 5204 | 5206 | 16 |

Those prefixes are the revert record for the shipped files; the edit produces copies, never in-place
changes to the install.

## 1. Which projectile archetype the launcher must point at

**`Projectiles.Batmobile_EMPMissile_Projectile_ForCars` — and both pointers already name it.** Keep them
as shipped; do not retarget to export 16, and do not delete export 16.

| reason | evidence | label |
|---|---|---|
| both payload pointers (`ProjectileArchetype` @2428, `ProjectileForCarsArchetype` @2492) resolve to export 5116 in all three packages, 6/6 | today's check above; `RBatmobileEMPMissile.g.cs:458` names `ProjectileForCarsArchetype`, `RPursuitModeMissileLauncher` declares the base pointer | decoded |
| `_ForCars` is the car-facing variant the class was built for (`CantFireOnPenguinVanDialogue`, `ProjectileForCarsArchetype`) | T-WP4c §2.2 | decoded |
| retargeting to export 16 would swap the whole object graph, not add a value: export 16's components (`RocketTrail`, `Mesh0`, `RB_RadialImpulseComponent`, `CollisionCylinder`) are its own outer objects, and its trail/explosion are the APC set (`FireTrail_APC`, `Batmobil_Rocket_Explosion`) instead of the car set (`FireTrail_Car`, `..._Explosion_Small`) | tag lists in `T-WP4d.md` §"Point 2"; today's dump | decoded |
| which of the two pointers the engine reads first is native and not in the packages — harmless here because both hold the same export, and the check asserts both so neither can drift | `RPursuitModeMissileLauncher.g.cs` declares the members, not the read order | UNKNOWN (read order) / safe |

Export 16 stays as the **donor of the four tags**, and stays unreferenced afterwards (proved by the
reverse scan; a new reference to it would mean a pointer was retargeted).

## 2. What is copied into `_ForCars`, and from where

Four tags, lifted from `Batmobile_EMPMissile_Projectile` (export 16) and spliced into export 5116's tag
stream in property-offset order.

| member (SDK) | offset | type | value | from | why |
|---|---:|---|---|---|---|
| `Projectile.MyDamageType` | 712 | `ClassProperty` (ObjectNCR) | `Core.RDmgType_BatmobileCannon` | 16 @712 | the only damage type BmAK ships on an EMP payload; without it the missile inherits the class default |
| `Projectile.Damage` | 728 | `FloatProperty` | `60.0` | 16 @728 | BmAK Immobiliser payload damage; the fired archetype has no scalar at all |
| `Projectile.DamageRadius` | 732 | `FloatProperty` | `0.0` | 16 @732 | single-target hit, not an area blast — matches the 60-damage/single-car reading |
| `RBatmobileMissile.ExlposionSound` | 968 | `ObjectProperty` (AkEvent) | `Ww_VFX_Tank_Explosion.Play_Batmobile_Immobiliser_Impact` | 16 @968 | the only *Immobiliser* asset in the weapon data; the fired archetype's only audio member is an `RAkAudible` **component** (@124) with no serialized event |

The SDK spells the sound member `ExlposionSound` (`RBatmobileMissile.g.cs:200`); that typo is the shipped
field name, not a transcription error here.

**Not copied, deliberately**

| member | sibling value | why not |
|---|---|---|
| `ExplosionTemplate` @960 | `Rocket.Batmobil_Rocket_Explosion` | `_ForCars` already ships `Rocket.Batmobil_Rocket_Explosion_Small` — the car-appropriate template; changing the look is a separate visual decision with no BmAK number behind it |
| `FireTrail` @808 | `Damage_States.FireTrail_APC` | `_ForCars` keeps `FireTrail_Car` for the same reason |
| `Projectile.MaxSpeed` @672 | 7500.0 | `_ForCars` inherits `Default__RBatmobileMissile` 10000.0; speed is not in this card's scope and the JC3 missile has its own velocity in the w618 tune |
| `RBatmobileMissile.AccelRate` @1064 | 40000.0 | same: class default 15000.0, and guidance numbers live in the JC3 tune (T-WP4) |
| `@992` / `@1016` (launch/flight AkEvents), `@824` bool, component refs | — | `_ForCars` has its own components and the REAL flight sounds are not this card's subject |

**The splice is proved, in memory, without writing a package**

```
$ cd E:/Modding/JC3-Batmobile && python - <<'PY'   (scratch, quoted in full in the transcript)
ForCars tag property order in the blob: [960, 1040, 1048, 840, 848, 808, 816, 704, 124, 180]
prefix 1 bytes: 00
walk end 81 blob 83 tail 0000
blob 83 -> 115 (+32 bytes)
re-walk: 14 tags, end 113 of 115 stop eof
  property @ 712 ObjectNCRProperty -> Core.RDmgType_BatmobileCannon (Class)
  property @ 728 FloatProperty    = 60.0
  property @ 732 FloatProperty    = 0.0
  property @ 968 ObjectNCRProperty -> Ww_VFX_Tank_Explosion.Play_Batmobile_Immobiliser_Impact (AkEvent)
TRANSPLANT PASS
```

Three facts this run establishes, each worth having before a writer exists:

1. the four tag byte runs are **self-contained** — the name indices and the `Core.*` / `Ww_*` object refs
   are package-local, so they lift from export 16 into export 5116 unchanged;
2. the tag stream is **not** sorted by property offset (shipped order starts 960, 1040, 1048, 840 …), so
   insertion position is free; the four tags were inserted at their semantic neighbours (712/728/732
   before 808, 968 after 960) and the walker still resolves all 14;
3. the export grows **83 → 115 bytes (+32)**, and the blob's 1-byte prefix and 2-byte tail are preserved.

**The blocker:** the repo has readers only. `Tools/scripts/upk_read.py` exposes no serializer, and the
nine `*upk*` scripts all read (`upk_read.py`, `_upk_any/_banks/_banksweep/_expfields/_exports/_summary/
_sweep/_tables.py`). Growing an export by 32 bytes moves every later export offset in a 17.9 MB
**chunked** package (header offset table + `PKG_TAG` chunk list + zlib/LZO sub-blocks), which no tool in
the repo writes. The BmSDK copy is not a substitute yet: managed code runs there, but 22 UObject/FName
addresses are still UNKNOWN for that build, so an in-memory property write is unproven
(`tmp/freebuff/reports/bmsdk-gog-copy-port.md` §3.2). Evidence level for the write itself: **UNKNOWN —
capability gap**, with the two routes named in §5.

## 3. The disable effect: nothing to copy

| search | result | label |
|---|---|---|
| every tag of `_ForCars` (10) and of the sibling (20) | no duration, no timer, no target-class filter, no "disable" member; the Emp-named data on either archetype is the impact sound only | decoded (absence) |
| `Default__RBatmobileMissile` (15 tags), `Default__RProjectile` (9), `Default__RBasicProjectile` (11) | nothing at 712/728/732/968 | decoded (absence) |
| the launcher class (`RBatmobileEMPMissile`, 21 tags) | no disable member either | decoded (absence) |
| where the disable lives | native: `RVehicleBatmobileBase.SetDisabledByEMP(bool)`, `DisabledByEMP`/`VulnerableToEMP`/`EMPMaterialIndex`; the only data-side EMP blast in either game is JC3's `EMP` pulse + `truck_emp.ftune` (100 dmg / 25 m, full radius) | decoded (state names) / UNKNOWN (the effect) |

So the payload edit carries **no disable**: it adds damage and the Immobiliser impact sound. The
file-backed EMP half is the JC3 side, and it is a shipped pattern rather than an invention — a
`CMissileWeaponBase`-owned `CForcePulse` exists 25 times in the fleet, each using that weapon's own blast
tune (`FORCEPULSE.md` §4.2), which is exactly the object B-06's `w618_sportsmuscle_missile_emp` clone can
carry. Keep that decision where T-WP4c put it (route R1); this card only makes the missile *hit* like the
Immobiliser.

## 4. BmAK lock-and-fire mapped onto `bInstantFire` and the AutoAim tune

| BmAK behaviour | decoded value and where | JC3 carrier | number already in the build | what the mapping preserves / loses |
|---|---|---|---|---|
| fires on the button, no spin-up | `bInstantFire` @2464 = **True** on `Batmobile_EMP_Missile_Launcher` in Batmobile/MK2/Funhouse (`RPursuitModeMissileLauncher.g.cs:238`) | no instant-fire member exists on `CMissileWeaponBase`; the decoded counterpart is the **absence** of a spin-up component — the handheld EMP `w702_emp` uses three `CBarrelSpinWeaponComponent`s for its dial, and the vehicle missile carries none (`EMP.md` §6) | the w618 clone's component list (B-06) | preserved: press → launch in the same frame. Build step is a "do not add", checked against the manifest's component list |
| launch point and tilt | `LaunchSocketName` = `BattleModeSpotLight`, `LaunchRotationOffset` @2452 = `[-3640, 0, 0]` = **-19.995°** pitch (3640/65536·360); the tracker's is `[5461,0,0]` = +29.998° (T-WP4d C5) | JC3 weapon point on the turret part (T-11 / `SOCKETS_JC3.json`) | B-05 weapon points | preserved: the missile leaves from the spotlight socket, angled down ~20°. The two gadgets deliberately differ by ~50°, so do not copy the tracker's rotator onto the launcher |
| lock before fire | `TagTarget` (`RVehicle`), `LockOnTarget`/`LastLockTarget` (`RVehicleNPC`), `LockOnTime` rising to `MissileLockOnDuration` **2.0 s** (`CivilianMissileLockOnDuration` 1.0) @2560/@2564 | JC3 has no tag and no lock-time member; the nearest instrument is the AutoAim envelope | `autoaim_batmobile_emp_lockon.wtunec` (B-06): `AngleThresholdNewTarget` 0.12 turns, `AngleThresholdCurrentTarget` 0.15 turns, `MaxAimDistance` **120.0 m** = BmAK `LockOnRange` 12000 UU (`WEAPONS.md:556`), `CanTargetVehicles` 1, `CanTargetRigidObjects` 1, `CanTargetCharacters` 0, in all six states | preserved: sticky aim on vehicles within 120 m, pedestrians refused. Lost: the 2.0 s lock gate and the tag's memory (T-WP4c C1). Setting all six states is deliberate — which state the Batmobile runs under is not decoded, so no state can silently keep -1 |
| a tagged car is remembered | `TagTarget` singular; `UnTagTarget`, `LoseLockTime`, `PromoteUntagPromptTime`, `UntagWarningEvent` `Play_HUD_fail` @2508 | no JC3 tag member (0/295 entity dumps carry `allegian`) | — | lost (C1). Not a payload problem: the fired missile's damage/sound do not depend on it |
| both mode buttons | `BattleModeFireButtonPressed(RVehicleNPC)` beside the pursuit path | forced slot root 4 (B-06) | manifest `key: emp` | preserved |

`bInstantFire` is True for the **Immobiliser**. It is **UNKNOWN for the tracker**: no `Vehicle_Tracker`
record serializes @2464 and no class default carries it (T-WP4d C1) — do **not** read the launcher's True
across to the tracker (that was the T-WP4c bug that produced the corrected card).

## 5. Build steps

| # | step | file | evidence level | revert |
|---|---|---|---|---|
| 0 | add a **tag-span** helper to the reader (`walk_tags` already records each payload at `at`, and `start = at - 4` for the simple tags used here; the splice test above validates it) | `Tools/scripts/upk_read.py` | decoded (today's transplant) | revert the function; the reader's outputs are unchanged |
| 1 | copy the three packages to a patch tree and keep the originals' sha256 (`f8c1e410…`, `620a6e18…`, `a3b784fa…`) | new `Working/EMP/modtag/` | decoded | delete the copies; originals never touched |
| 2 | re-serialize export 5116/5167/5206 with the four tags (+32 bytes), rewrite the export offset table for every later export, re-chunk and re-compress the container | new writer, e.g. `Tools/scripts/upk_write_tags.py` | **UNKNOWN — no writer exists** (§2). Route A: byte-level container writer. Route B: BmSDK runtime property write (`Projectile.Damage`, `MyDamageType`, `ExlposionSound` are ordinary properties), which needs the 22 UNKNOWN UObject addresses first | restore the copied packages |
| 3 | do **not** add a spin-up component; keep the missile's `missile_weapon[0]` tuning and the six-state AutoAim tune as B-06 wrote them | `Working/Weapons/manifest.json` | decoded (manifest readback `ok: true`) | B-06's own revert (private paths) |
| 4 | run the check (below) on the patched packages | `Tools/scripts/wp4_emp_payload_check.py` | decoded | — |
| 5 | 5-minute experiment before step 2 is automated: repeat the splice in memory for MK2 and Funhouse and confirm 14 tags each (the three packages are byte-identical in these fields per T-WP4d, but the check must not assume it) | scratch | decoded | — |

Intended change for the one file I added: `Tools/scripts/wp4_emp_payload_check.py` is new and read-only
(opens the three packages, writes only `Working/Weapons/emp_payload_check.json`); it is the correct place
because the V-02 and T-WP4d generators are pinned to other cards and this check must be re-runnable after
the payload edit. Revert: delete the script and the JSON snapshot.

## 6. The check that proves the pointers after the edit

`Tools/scripts/wp4_emp_payload_check.py` — 19 assertions, exit 0 only when all pass:

| assertion | per package | baseline today |
|---|---|---|
| launcher @2428 → `Projectiles.Batmobile_EMPMissile_Projectile_ForCars` | 3 | PASS |
| launcher @2492 → same | 3 | PASS |
| fired @728 `Damage` = 60.0 | 3 | FAIL |
| fired @732 `DamageRadius` = 0.0 | 3 | FAIL |
| fired @712 `MyDamageType` = `Core.RDmgType_BatmobileCannon` | 3 | FAIL |
| fired @968 `ExlposionSound` = `Ww_VFX_Tank_Explosion.Play_Batmobile_Immobiliser_Impact` | 3 | FAIL |
| orphan export 16 has 0 incoming refs (`--reverse`) | 1 | PASS |

```
python Tools/scripts/wp4_emp_payload_check.py --reverse; echo "EXIT=$?"   # must print CHECK PASS, EXIT=0
```

It also prints the invariants that must not move: launcher tag count 21, `bInstantFire` True,
rotator `[-3640, 0, 0]`, and the fired archetype's tag count (10 → 14) and size (83 → 115). A change in
any of those is a failed edit even if the four payload rows read correctly.

## 7. Every UNKNOWN, with the file that settles it

| # | UNKNOWN | searched | file/route that settles it |
|---|---|---|---|
| U1 | the **damage the fired missile actually applies** before the edit (export 5116 has no `Damage`; the class-default chain 712/728/732 is empty in all three CDOs) | 10 + 20 + 15 + 9 + 11 tags; `T-WP4d.md` §UNKNOWNs 1 | the non-cooked `RBatmobileMissile`/`RProjectile` CDO (engine binary, not in `CookedPCConsole`), or a runtime sample of a missile hit (`Tools/scripts/bmak_runtime_sampler.py`). After the edit the value is ours, so this only matters for the before/after comparison |
| U2 | the **impact sound actually played** by the fired archetype today | same | same route; the fired archetype's `RAkAudible` @124 is a component with no serialized event |
| U3 | the **disable** — duration and look | every member of both projectiles and the launcher; both CDOs | native `RBatmobileEMPMissile.ProjectileHitActor` / `SetDisabledByEMP`; settled by the in-game card (§8) or by disassembling that function |
| U4 | the **tracker's** `bInstantFire` | `Vehicle_Tracker` in 4 packages (0 carriers of @2464), `Default__RBatmobileVehicleTracker` (5 tags, none 2464) | runtime read of the CDO at offset 2464 through the BmSDK sampler — not a package file |
| U5 | which payload pointer the engine reads first (@2428 vs @2492) | `RPursuitModeMissileLauncher.g.cs` declares both, no read order | native; harmless because both name export 5116, and the check asserts both |
| U6 | whether the **container writer** can grow an export by 32 bytes and keep the package loadable | no writer in `Tools/scripts` (9 readers); BmSDK copy has 22 UNKNOWN addresses | the writer built in step 2 + a load test; this is the plan's single blocker |
| U7 | whether the JC3-side pulse (`truck_emp.ftune`) disables a car | `EMP.md` §2/§8: no pointer from the trigger to the pulse; no member names the target class | in-game test (T-WP4c route R1); not part of this edit |

Nothing above is filled in with a plausible value: U1/U2 are the reason the four tags are **copied** from
the only BmAK record that carries them rather than invented.

## 8. Pilot card

> **Fire the Immobiliser from the locked launcher at a civilian car 60-100 m ahead in pursuit mode: the
> missile leaves on the frame the button goes down (no spin-up), and its single impact plays exactly one
> Immobiliser impact sound and takes 55-65 units of the car's damage budget with no splash on a second
> car beside it; pass = immediate launch, one impact sound, 55-65 damage on the aimed car and 0 on its
> neighbour, fail = a charge-up delay, no impact sound, 0 damage, or any damage to the neighbouring car.**

Pass band: 55-65 damage (`Projectile.Damage` 60.0, band ±5 for rounding and any armour multiplier), one
impact event, 0 damage on a car 3 m to the side (`DamageRadius` 0.0). The disable is judged separately
(U3): if the car keeps driving after the hit, the payload is still correct — the disable is the JC3 pulse,
not this archetype.
