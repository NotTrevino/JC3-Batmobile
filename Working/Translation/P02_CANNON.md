# P-02 — what raises and lowers the Batmobile cannon, and where −5…20° comes from

**Question.** P-02 is the cannon, `no-sequence` in `PARTS_ANIM_COVERAGE.md`. Which BmAK mechanism
raises/lowers it in battle mode — socket, bone, skeleton control, AimOffset or AnimTree node — and is
the −5…20° pitch range in the translation row a file value?

**Answers.**

1. **The cannon is aimed by code on the weapon object, not by animation, a skeletal control or an
   AnimTree node.** BmAK's `RBatmobileCannon` carries `CannonPitchBone` (FName, offset 2408),
   `TargetGunRotation` (Rotator, 2628), `GunYawOffset` (int, 2624), the aim switches
   `bDisableCannonAimAtTargets` / `bNonAimedCannonIsCameraRelative`, and its pitch limits
   `MinTurretPitch` **0.0** (`0x0B5C`) and `MaxTurretPitch` **18.0** (`0x0B60`)
   (`Research/BatmobileGrab/BMSDK_OFFSETS.json`, values in `WEAPONS.md:768-769`). The heavy-cannon
   object adds `FirePitchOffset` **350** (`0x09A4`), `RecoilImpulsePitch`, `LockOnAngle` and
   `ChaingunAimOffset` **[0.0, 0.0, −50.0]** (`0x0B0C`). So the pitch is a script-side rotation of a
   **named bone** driven by the weapon's target rotation and clamped by its own min/max pitch.
2. **`−5…20°` is a file value — from the JC3 donor carrier, not from BmAK.** It is the shipped hinge on
   `mediumtank_cannon`: `Research/JC3Grab/TURRET.json`, `samples[0].constrained_parts[0]` —
   `behavior "Cannon"`, `hinge.class "hkpLimitedHingeConstraintData"`, `axis [1.0, 0.0, 0.0]`,
   `min_deg -5.0` / `min_rad -0.087266`, `max_deg 20.0` / `max_rad 0.349066`, `pivot [0.0, 2.5347,
   0.0]`, `size 304`, `damage_type "Land_Generic"`, carried by
   `editor/entities/jc_vehicles/01_land/v0201_car_capstone_mediumtank/v0201_car_capstone_mediumtank_military_01.ee`.
   `T8_PARTS.md:47` names that entity in the row, `Working/Parts/JOINT_FIELDS.md:79-80,113` records the
   same range converted to radians and labels the provenance `constraint_source: P-02 carrier hinge`,
   and `bm_physicsc_hinges.py:11` writes `-0.087266 … 0.349066 rad` into RC3's hinge 12.
3. **BmAK's own cannon pitch limits are 0 … 18°, not −5 … 20°.** The two numbers come from different
   files for different reasons: −5…20° is the JC3 tank hinge the build copies, 0…18° is BmAK's
   `RBatmobileCannon` archetype. Any claim that −5…20° is "BmAK's own" would be wrong; any claim that
   the translation row invented it would also be wrong.

## 1. The bones and the socket

| item | evidence |
|---|---|
| `Batmobile_Rig_Weapons_Heavy_Cannon_Barrel_01` — bone #103, parent `Batmobile_Rig_Weapons_Turret_Top`, bind origin (0.000, 1.702, 0.018) | `Research/BatmobileGrab/BONES.md:145` |
| `Batmobile_Rig_Weapons_Heavy_Cannon_Barrrel_02` — bone #104, parent `…_Barrel_01`, same origin (the triple-r spelling is the shipped name) | `BONES.md:146` |
| `CannonMuzzle` socket on `Batmobile_Rig_Weapons_Heavy_Cannon_Barrrel_02`, local (0.000, 1.702, −0.456), direction (0.000, −0.000, −1.000), group `weapons`, `mounted on a bone: yes` | `Research/BatmobileGrab/SOCKETS_JC3.md:82,144` |

The socket is a **muzzle marker**, not the pitch carrier: it sits on the outer barrel bone, so it
follows whatever the bone does — but nothing in the socket data rotates it.

## 2. What the animation actually does (why the row is static)

`Batmobile_V2_Cannon_Fire` (`Playable_Batmobile_SF` export 216, 0.7 s) moves 12 bones and **no
rotation about the pitch axis**: `Batmobile_Rig_Weapons_Heavy_Cannon_Barrel_01` translates 36.129 cm and
`…_Barrrel_02` translates 53.376 cm. There is no pitch keyframe to copy, which is why
`T8_PARTS.md:79-82` calls the row static and why `PARTS_ANIM_COVERAGE.md:35` lists it `no-sequence`.
The `T8` static reason is about **animation**, not about the hinge: the row still carries the shipped
−5…20° hinge, which is exactly the "WEAK" reading card T-12's A6 records
(`Research/challenge/card-T-12.md:70,219-224`).

## 3. Skeletal controls, AimOffsets and AnimTrees in the cooked packages

| route | result |
|---|---|
| AnimTrees in the four Batmobile packages | 3 trees (`Batmobile_Skel_Ctrl_Door` in SF/export 244 and MK2/243, `Batwing_Vehicle_AnimTree` in Joker/485). Children are `AnimNodeSequence`; the only controls are **3× `RSkelControl_FeedConstraint`** on `Flappy_Rear_Door_Btm_Rot` and the two `*_Power_Cell` bones. **None touches the cannon** (`Research/BatmobileGrab/ANIMATIONS.json`, `trees[]`) |
| `AnimNodeAimOffset` | exists **only as a class name in `Engine.upk`** (one export, the class default) across the 324 packages searched; it is not instantiated in any Batmobile package, and no AimOffset asset names a cannon bone (`tmp/freebuff/scratch/p13_upk.json`, package `Engine.upk`) |
| `CannonPitchBone` | the member exists in `RBatmobileCannon` at offset 2408, but **its FName value is not in the dumps** (`WEAPONS.md`/`WEAPONS.json` carry no value row for it), so *which* bone it names is UNKNOWN here. The cannon bones in §1 are the only two cannon bones in the skeleton, so at most it could name one of them or their parent |
| weapon-side "launch rotation" | `RBatmobileHeavyCannon.FirePitchOffset` = **350** (IntProperty, `0x09A4`) and `ChaingunAimOffset` = **[0.0, 0.0, −50.0]** (Vector, `0x0B0C`) are the only rotation-shaped weapon values in `WEAPONS.md:960,982`. `FirePitchOffset`'s unit is **UNKNOWN** (an int with no SDK unit note); it is not a pitch limit, and −5…20° does not appear anywhere in `WEAPONS.md` |

So: no AimOffset, no skeletal control, no AnimTree node raises the cannon. The mechanism class is
**code-driven bone rotation from the weapon object** (`TargetGunRotation` + `CannonPitchBone`,
clamped by `MinTurretPitch`/`MaxTurretPitch`), with `FirePitchOffset`/`ChaingunAimOffset` as
fire-time offsets.

## 4. Does −5…20° come from a file value? Yes — cite

| value | file | path | number |
|---|---|---|---|
| min pitch | `Research/JC3Grab/TURRET.json` | `samples[0].constrained_parts[0].hinge.min_deg` | **−5.0** (`min_rad −0.087266`) |
| max pitch | same | `…hinge.max_deg` | **20.0** (`max_rad 0.349066`) |
| axis | same | `…hinge.axis` | `[1.0, 0.0, 0.0]` |
| class | same | `…hinge.class` | `hkpLimitedHingeConstraintData` |
| pivot | same | `…hinge.pivot` | `[0.0, 2.5347, 0.0]` |
| carrier entity | `T8_PARTS.md:47` and `TURRET.json` `point_census.cross_entity` | — | `v0201_car_capstone_mediumtank_military_01.ee` (owner `…_debug.ee`, weapon `w602_mediumtank_canon`, 3 owners) |
| converted, provenance-labelled | `Working/Parts/JOINT_FIELDS.md:79-80,113` | — | −5..20° = −0.087266..0.349066 rad, `constraint_source` "P-02 carrier hinge" |

It is a **JC3 file value**, is what RC3's hinge 12 stores, and is *not* a BmAK value. BmAK's own
comparable numbers, for contrast:

| BmAK member | value | source |
|---|---|---|
| `RBatmobileCannon.MinTurretPitch` | 0.0 | `WEAPONS.md:768` (`0x0B5C`) |
| `RBatmobileCannon.MaxTurretPitch` | 18.0 | `WEAPONS.md:769` (`0x0B60`) |
| `RBatmobileHeavyCannon.FirePitchOffset` | 350 | `WEAPONS.md:960` (`0x09A4`) |
| `RBatmobileHeavyCannon.ChaingunAimOffset` | [0.0, 0.0, −50.0] | `WEAPONS.md:982` (`0x0B0C`) |

## 5. Consequence and UNKNOWNs

- The build's cannon hinge (−5…20° about +X) is correctly sourced from JC3's `mediumtank_cannon`, not
  from BmAK, and the row's `static` label refers to the absence of an animated pitch, not to the hinge.
  If a BmAK-matched limit were wanted instead, the file value would be **0…18°** — a different row, not
  a correction to this one.
- **UNKNOWN:** which bone `RBatmobileCannon.CannonPitchBone` names (member offset known, value not
  dumped); the unit and effect of `FirePitchOffset` 350; whether BmAK's cannon pitch is clamped by
  `Min/MaxTurretPitch` at runtime or by code elsewhere (`RVehicleWeapon.MaxAimX/MaxAimY` are related
  members, offsets 2156/2160).
- **Not re-decoded here:** the weapon archetype payloads themselves — every number above is read from
  the existing dumps (`WEAPONS.md`/`WEAPONS.json`, `BMSDK_OFFSETS.json`, `TURRET.json`), not from a new
  package walk.
