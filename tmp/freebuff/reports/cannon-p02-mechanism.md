**STATUS: DONE — mechanism is a code-driven bone rotation on the weapon object; the −5…20° pitch range is a file value, but a JC3 one (`TURRET.json`), not a BmAK one.** BmAK's own `RBatmobileCannon` limits are `MinTurretPitch` 0.0 / `MaxTurretPitch` 18.0. Page: `Working/Translation/P02_CANNON.md`.

# P-02 cannon — report

**Answer to the card.** The cannon is not raised by an animation, a skeletal control, an AimOffset or an
AnimTree node. It is aimed by script on the weapon object: `RBatmobileCannon.CannonPitchBone` (FName,
offset 2408) plus `TargetGunRotation` (Rotator, 2628), clamped by `MinTurretPitch` 0.0 (`0x0B5C`) and
`MaxTurretPitch` 18.0 (`0x0B60`), with `RBatmobileHeavyCannon.FirePitchOffset` 350 (`0x09A4`) and
`ChaingunAimOffset` [0,0,−50] (`0x0B0C`) as fire-time offsets. The −5…20° in the translation row **is** a
file value: `Research/JC3Grab/TURRET.json` `samples[0].constrained_parts[0]` — the shipped hinge on
`mediumtank_cannon` in `v0201_car_capstone_mediumtank_military_01.ee`, axis [1,0,0],
`min_deg −5.0`/`min_rad −0.087266`, `max_deg 20.0`/`max_rad 0.349066`, `hkpLimitedHingeConstraintData`.

## Evidence table

| claim | file / line |
|---|---|
| pitch limits 0.0 / 18.0 on BmAK's cannon | `Research/BatmobileGrab/WEAPONS.md:768-769`; `BMSDK_OFFSETS.json` `RBatmobileCannon` 0x0B5C/0x0B60 |
| aim members (`CannonPitchBone`, `TargetGunRotation`, `GunYawOffset`, aim switches) | `BMSDK_OFFSETS.json` `RBatmobileCannon` offsets 2396-2912 |
| fire-time offsets 350 and [0,0,−50] | `WEAPONS.md:960,982`; `WEAPONS.json` objects[34] fields[4]/[26] |
| cannon bones #103/#104, bind origins, parents | `Research/BatmobileGrab/BONES.md:145-146` |
| `CannonMuzzle` socket on `…_Barrrel_02`, local (0,1.702,−0.456), dir (0,0,−1), mounted yes | `Research/BatmobileGrab/SOCKETS_JC3.md:82,144` |
| no rotation animated: Fire sequence translates 36.129 cm / 53.376 cm | `T8_PARTS.md:79-82`; `PARTS_ANIM_COVERAGE.md:35`; `ANIMATIONS.json` `Batmobile_V2_Cannon_Fire` (SF/216, 0.7 s, 12 moved bones) |
| only skel controls in the Batmobile trees are 3× `RSkelControl_FeedConstraint` | `ANIMATIONS.json` `trees[]` |
| `AnimNodeAimOffset` exists only as a class default in `Engine.upk` | `tmp/freebuff/scratch/p13_upk.json` |
| the −5..20° hinge and its carrier entity | `Research/JC3Grab/TURRET.json` `samples[0].constrained_parts[0]`, `point_census.cross_entity`; `T8_PARTS.md:47` |
| rad conversion + provenance label | `Working/Parts/JOINT_FIELDS.md:79-80,113`; `Tools/scripts/bm_physicsc_hinges.py:11` |
| the row's "static" is about animation, not the hinge (card's own A6 caveat) | `Research/challenge/card-T-12.md:70,219-224` |

## UNKNOWNs

- Which bone `CannonPitchBone` names — the member offset is known (2408) but no value row for it exists
  in `WEAPONS.md`/`WEAPONS.json`, so the FName is not dumped.
- The unit/effect of `FirePitchOffset` 350 (int, no SDK unit note).
- Whether runtime clamping is `Min/MaxTurretPitch` or code elsewhere (`RVehicleWeapon.MaxAimX/MaxAimY`,
  offsets 2156/2160).
- No new package walk was made: the numbers are read from the existing dumps, so this page inherits
  their coverage limits.

## Deliverables and side effects

- `Working/Translation/P02_CANNON.md` (new page).
- `tmp/freebuff/reports/cannon-p02-mechanism.md` (this report).
- Nothing was edited: no script, research record, build or game file. All reads were of repo files.
