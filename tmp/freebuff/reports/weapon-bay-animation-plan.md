# Weapon bays — BmAK deploy/retract timings vs JC3 weapon-mount hooks

Status: research + values. BmAK numbers re-read from `Research/BatmobileGrab/ANIMATIONS.json`
(command in §8) and cross-checked against `Working/Translation/T8_PARTS.md` P-03/P-05/P-07/P-08;
JC3 from `Research/JC3Grab/TURRET.md`, `TURRET_LIMITS.md`, `WEAPON_WIRING.md`, `MOVING_PARTS.md`,
`DOORS.md`, `EMP.md`, `SIGNATURE_DIFF.md`, `USAGES.md`, `FX13_CASINGS.md`, `LIGHTS_FORENSICS.md`,
`README.md`; build state from `Working/Parts/bm_vehicle_parts.json`.

## 0. Verdict

| bay | BmAK deploy | BmAK retract | JC3 hook | value we set |
|---|---|---|---|---|
| **missile pods** | `Batmobile_V2_Missles_Up` — 26 f, **0.833 s** | `Batmobile_V2_Missles_Down` — 26 f, **0.833 s** | `MissileHatch` door behaviour + a Havok limited hinge (fleet: 16 rows, all 0..150° about ±Z) | hinge **0…15°**, pivot at the pod hinge, axis **±Z**; open/close **0.833 s** each; pod bones 14.988°, mid-shell slide 10.866 cm |
| **Vulcan (chain gun)** | **none** — the barrels only spin | **none** | `GatlingGun` rotating part driven by `weapon_rpm` (`rotating_parts[]`: axis, blades, `rpm_multiplier`, visibility rpm) | `rpm_multiplier` **1.0**, 6 blades, axis = the joint's **+X**; **2160° / 3.933 s** = 553.8 °/s average (92.3 rpm), peak **1229.51 °/s** (204.9 rpm) |
| **cannon** | no deploy clip; the barrels **recoil 53.376 cm** in `Cannon_Fire` (0.700 s) | reload feed `Cannon_Reload_Left/Right`, **0.467 s** | `Cannon` behaviour part on an X hinge (donor: -5…+20°, pivot (0, 2.5347, 0)); `SWeaponPoint` fire point names yaw+pitch parts | pitch hinge **-5…20°**, no pitch animation; recoil is **translation, not reproducible**; fire clip **0.700 s**, reload **0.467 s** |
| **whole weapon array (the actual "bays")** | `Tank_Spread_Open` — 61 f, **2.000 s** (`Weapons_Trans` 68.51 cm, `Top_Sides_Root` 69.78 cm, `Riot_Sup_Arm_01` 123.92°) | `Tank_Spread_Close` — 61 f, **2.000 s** (arm 120.01°) | hinged parts only — every one is a hinge, none translates; `_partswap` is a **second LOD/part**, not a runtime swap | 2.000 s each way is an acceptance criterion, not a file value: JC3 stores **no duration anywhere** |

**The one-line answer on hooks:** JC3 has **no weapon animation and no part-swap call**. A weapon
moves because a *part* it is bolted to has a behaviour with a mechanism — a `Turret`/`Cannon`/
`MissileHatch` behaviour on a Havok hinge, or a `GatlingGun`/`EngineRotatingPart` row in
`rotating_parts[]` driven by an rpm variable. The only "swap" is a second part whose model LOD
carries a `_partswap` suffix (one shipped example: the EMP flatbed's core), i.e. an **authored
alternate state**, not a callable transition.

## 1. BmAK — every deploy/retract clip, timed

All rows are package label `Batmobile`; each clip exists **identically in all four packages**
(base, MK2, Funhouse, Joker — `ANIMATIONS.md` §4), so one set of numbers covers every skin.

| clip | AnimSet | frames | **length s** | tracks | notifies | what moves |
|---|---|---:|---:|---:|---:|---|
| `Batmobile_V2_Missles_Up` | `Batmobile_V2_Pose_States` | 26 | **0.833** | 7 | 0 | `Missiles_L/R_T` + `L/R_B` 14.988°; `L/R_Mid` 10.8658 / 10.8634 cm |
| `Batmobile_V2_Missles_Down` | `Batmobile_V2_Pose_States` | 26 | **0.833** | 27 | 0 | same bones, same extents |
| `Batmobile_V2_Tank_Spread_Open` | `Batmobile_V2_Pose_States` | 61 | **2.000** | 74 | 3 | `Weapons_Trans` 68.5082 cm, `Top_Sides_Root` 69.783 cm, `Heavy_Shells` 68.122 cm, `Riot_Sup_Arm_01` 123.919°, `Riot_Sup_Main` 104.481°, `Machine_Gun_01` 179.995°, `Mine_Cover_01` 65.0° |
| `Batmobile_V2_Tank_Spread_Close` | `Batmobile_V2_Pose_States` | 61 | **2.000** | 74 | 3 | same, `Riot_Sup_Arm_01` 120.005° |
| `Batmobile_V2_Tank_Spread_Open_Game` | `Batmobile_V2_Pose_States` | 61 | **2.000** | 70 | 12 | as Open but `Riot_Sup_Arm_01` 124.791°, `Riot_Sup_Main` 108.738° |
| `Batmobile_V2_Tank_Spread_Close_Game` | `Batmobile_V2_Pose_States` | 61 | **2.000** | 70 | 15 | as Close |
| `Batmobile_V2_Cannon_Fire` | `Batmobile_V2_Pose_States` | 22 | **0.700** | 74 | 0 | `Heavy_Cannon_Barrrel_02` **53.376 cm**, `Barrel_01` 36.1293 cm, `Weapons_Trans` 45.8677 cm, `Machine_Gun_Root` 2.281°, `Riot_Suppressor_Root` 2.99° |
| `Batmobile_V2_Cannon_Reload_Right` | `Batmobile_V2_Pose_States` | 15 | **0.467** | 57 | 0 | shell tween bones, max `R_Shell_Tween_001` 14.6518 cm / 79.75° |
| `Batmobile_V2_Cannon_Reload_Left` | `Batmobile_V2_Pose_States` | 15 | **0.467** | 56 | 0 | `L_Shell_Tween_001` 14.6513 cm / 77.5° |
| `Batmobile_V2_ChainGun_Spin` | `Batmobile_V2_Pose_States` | 119 | **3.933** | 73 | 0 | `Machine_Gun_02` 179.496° (a ±180 wrap = **2160° = 6 turns** over the clip, T8 P-03) |
| `Batmobile_V2_Turret_Spin` | `Batmobile_V2_Pose_States` | 79 | **2.600** | 74 | 0 | `Weapons_Turret_Root` 60.001° |
| `Drive_To_Combat` | `BM_Batmobile_Chassis` | 61 | **2.000** | 75 | 0 | the whole transformation (weapons, arches, jet) |

Rates derived from those pairs:

* missile pods **14.988° / 0.833 s = 17.99 °/s** mean; the top bones peak at **32.14 °/s** and the
  bottom at **75.10 °/s** (T8 P-07), so the pods snap faster at the bottom than the top.
* weapon spread **123.919° / 2.000 s = 61.96 °/s** on the riot-suppressor arm (peak in T8: 47.21 °/s
  on the part's own pivot, 315.39 °/s on the child ammo bone).
* turret **60.001° / 2.600 s = 23.08 °/s** mean, peak **174.05 °/s** (T8 P-01).
* chain gun **2160° / 3.90 s = 553.85 °/s = 1.538 rev/s ≈ 92.3 rpm**, peak **1229.51 °/s ≈ 204.9 rpm**
  (T8 P-03). The clip is 3.933 s at 30 fps.
* cannon reload **0.467 s** per side, shell bone sweeping 79.75° in that time = **170.7 °/s**.

### 1.1 What each bay actually *is*

* **Missile pods** are a genuine **deploy/retract pair** (`Up`/`Down`, 0.833 s each): four pod
  bones lift 14.988° and the mid shell slides 10.866 cm. This is the only clean two-state bay in
  the car.
* **Vulcan** has **no deploy**. The gun lives inside the body shell; the only motion is spin
  (`ChainGun_Spin`) plus a 2.281° nudge of `Machine_Gun_Root` during `Cannon_Fire`. There is no
  `ChainGun_Up`/`_Down` clip in the 253 sequences.
* **Cannon** has **no deploy either**. Its barrels *translate* (53.376 cm / 36.129 cm) during fire
  and the feed moves shells in 0.467 s. T8 P-02 records it as `static` because a hinge cannot
  reproduce translation.
* **The bays themselves** (the plates the weapons rise out of) open with `Tank_Spread_Open` /
  `Close`, 2.000 s, together with `Top_Sides_Root` (69.783 cm), `Weapons_Trans` (68.508 cm) and
  `Heavy_Shells` (68.122 cm) — one 2-second transformation, not a per-weapon animation.
  `_Game` variants carry 12/15 notifies (sound/script) where the plain ones carry 3.

**Notifies** matter here: the plain spread clips have **3** notifies and `_Game` has **12 / 15**,
so the scripted (gameplay) version is the one that animates the weapon HUD/audio beats. The
missile and spin clips have **0** notifies — nothing in them tells the game a bay opened.

## 2. JC3 — where a weapon mount can move

**A turret is two parts and two Havok hinges** (`TURRET.md`): yaw part behaviour `Turret`, pitch
part behaviour `Cannon`, each a `hkpLimitedHingeConstraintData` in `.physicsc`; the weapon's fire
point names **both** parts in two unnamed string properties.

| vehicle | yaw part | yaw limits | pitch part | pitch limits | weapon |
|---|---|---|---:|---|---:|
| medium tank v0201 | `mediumtank_turret` | **-179…179°** | `mediumtank_cannon` | **-5…20°** | `w602_mediumtank_canon` |
| Bavarium tank v0202 | `bavariumtank_turret` | -179…179° | `bavariumtank_cannon` | -5…20° | same tune |
| small tank v0603 | `smalltank_turret` | -179…179° | `smalltank_cannon` | (own) | `w605_smalltank_canon` |
| APC v0200 | `apc_turret_base` | -179…179° | `apc_weapon_mount_vertical` | **-15…50°** | `w206_mounted_capstone_m2hm` |
| armoured jeep v0600 | `armoredjeep_turret_base` | -179…179° | `armoredjeep_weapon_mount_vertical` | -25…50° | `w206` |
| technical v0504 | `technicaljeep_rebel_turret` | -179…179° | `technicaljeep_weapon_mount_vertical` | -10…45° | `w206` |
| corvette | `corvette_turret` | -150…150° | `corvette_gun` | -5…75° | `w616_corvette_canon` |
| heavy patrol | `heavypatrol_weapon_mount_l_horizontal` | -75…75° | `…_l_vertical` | -50…50° | `w206` ×2 |

**The weapon → part link** (`WEAPON_WIRING.md`, `TURRET.md` §1): each weapon sits in a **slot**
(`main_weapon`, `mounted_weapon`, `mounted_weapon_2`, `internal.fire_point.N`), and the loadout line
lists its class, id, muzzle count, aim component and **mount parts**. The medium tank's
`fire_position_0` carries the two mount-part names; the missile subtree of the Serpente is
1 `CMissileWeaponBase` on `main_weapon`, **4 `internal.fire_point.N` tubes** at y 1.085 / z −1.566,
4 `SAttachedEffect` muzzles all pointing at `sportsmuscle_missile_muzzleflash.effc`, plus
`CAimPOIWeaponComponent`, `CForcePulse` and `CMaterialEffectTable` (`README.md` §, `SIGNATURE_DIFF.md`).

**Rotation hooks** (`MOVING_PARTS.md` §1/§3, 47 rows in 22 of 78 modules):

| behaviour | driving variable | row stores |
|---|---|---|
| `GatlingGun` | **`weapon_rpm`** | `part_index`, `rotation_axis[3]`, `number_of_blades`, `rpm_multiplier`, `min/max_rpm_visible`, `rpm_opacity_transition`, `position[3]` |
| `EngineRotatingPart` | `engine_rpm` | same |
| `Rotor` / `Propeller` / radars | `rotor_rpm` / `propeller_rpm` / `radar_*_rpm` | same |

`GatlingGun` ships on **24 parts / 12 entities / 3 chassis, all `CBoat`/`CHelicopter`** — it is
**unproven on a `CCar`**. `EngineRotatingPart` is proven on a `CCar` (v0506 tractor fan) and is the
one rotating behaviour with a car precedent. `rotoscope_rpm_per_cycle` is 20.0 on `GatlingGun`.

**Door hooks for a bay:** `MissileHatch` is a door behaviour with **16 rows on exactly one vehicle**
(the monorail missile car, all 0..150° about ±Z). Nothing in that entity opens them — no
interaction, no attached effect, no weapon member names a hatch; the opening is code (`DOORS.md`
§3). For a car the only shipped `MissileHatch` precedent is therefore a **CTrain**, not a `CCar`.

**Part-swap hook:** the one shipped example is `oldtruck_emp_device_core_rebel_partswap` — a
**second part (index 47)** beside the core (46), both children of part 5, with its own
`..._partswap.lod` (`EMP.md` §2, `MODLOG.md` §). It is a model variant selected as a part, not a
runtime swap call; nothing in the entity chooses between them.

**Fire/effect hook:** `SAttachedEffect` with `Usage` = **`Fire`** (5,342 objects, hash 4131019937)
is how a muzzle flash is hung on the weapon; `FX13_CASINGS.md` shows a casing object whose `Usage`
is literally the string `Fire`, i.e. effects fire on the weapon event, not a timer. Muzzle flashes
are separate `.effc`, e.g. `sportsmuscle_missile_muzzleflash.effc` (the donor's own) and
`rico_50cal_muzzleflash.effc` (21 vehicle carriers).

**No animation exists on the vehicle side at all**: the donor's `.epe` is 566 members and holds
**0 animation files** (`DOORS.md` §4); every motion is part + mechanism + code.

## 3. Timings we set

Nothing on the JC3 side stores a duration. The table gives the two things a file *can* hold —
hinge limits / rpm — and the durations as acceptance criteria.

| bay | file value | duration to verify | angle/rate source |
|---|---|---|---|
| **missile pods (hatch)** | hinge **0…15°**, axis **±Z** (fleet `MissileHatch` axis), pivot at the pod hinge | **0.833 s** up, **0.833 s** down | 14.988° in 0.833 s (top 32.14 °/s, bottom 75.10 °/s) |
| **missile pod shells** | `hinged_parts[]` row on the pod part, no extra limit | same clip | 4 pod bones |
| **Vulcan** | `rotating_parts[]`: axis = joint **+X** (JC3 `[-0, 0, -1]` in T8), **6 blades**, `rpm_multiplier` **1.0**, visibility `-1…-1` | 6 turns in **3.90 s** → **92.3 rpm** average, **204.9 rpm** peak | `weapon_rpm` drives it; BmAK 2160° / 3.90 s |
| **cannon pitch** | hinge **-5…20°**, axis **+X**, pivot (0, 2.5347, 0) (donor values) | no pitch clip — aim only | `mediumtank_cannon` |
| **cannon recoil** | *cannot be authored* — 53.376 cm is translation | fire cycle **0.700 s** | `Cannon_Fire` |
| **cannon reload** | *cannot be authored* — shell feed is bones only | **0.467 s** per side | `Cannon_Reload_L/R` |
| **turret yaw** | hinge **-179…179°**, axis **+Y**, pivot at the ring | spin clip **2.600 s** for 60.001° | `Turret_Spin`, peak 174.05 °/s |
| **weapon-array bays** | hinges only; the 68–70 cm slides of `Weapons_Trans` / `Top_Sides_Root` / `Heavy_Shells` are **lost** | open **2.000 s**, close **2.000 s** | `Tank_Spread_Open/Close` |
| **mine covers** | hinge **0…65°** | inside the 2.000 s spread | `Mine_Cover_01` 65.0° |
| **riot-suppressor arm** | hinge **0…124°** (max of the two variants) | inside the 2.000 s spread | 123.919° plain / 124.791° `_Game` |

Two design consequences to state plainly:

1. **The bay motion is the part, not the weapon.** If the missile pods are not cut as their own
   part with a hinge, no weapon hook moves them; the `MissileHatch` behaviour on a `CCar` is
   **unproven** (its only 16 shipped rows are on one train), so this is a Q-1 probe as much as a
   build step.
2. **`GatlingGun` is unproven on a car.** `EngineRotatingPart` is the proven car precedent. Both
   are driven by a *vehicle rpm variable*, so whichever is chosen the spin is code-timed: BmAK's
   3.90 s / 6 turns sets `rpm_multiplier` and the 92.3 rpm working point, and nothing can force
   the 204.9 rpm peak.

## 4. Which of the four weapon systems can be reproduced at all

| BmAK motion | kind | JC3 mechanism | verdict |
|---|---|---|---|
| missile pods lift 14.988° | rotation | hinge (`MissileHatch`) | **reproducible** |
| missile mid shell slides 10.866 cm | translation | none | **lost** |
| weapon array slides 68–70 cm | translation | none | **lost** |
| riot-suppressor arm 124° | rotation | hinge | **reproducible** |
| mine covers 65° | rotation | hinge | **reproducible** |
| Vulcan spin 2160° | rotation | `rotating_parts[]` + rpm | **reproducible** (unproven behaviour on a car) |
| cannon recoil 53.376 cm | translation | none | **lost** |
| cannon reload 79.75° shell feed | rotation + translation | hinge only | **partly** |
| turret spin 60° | rotation | hinge | **reproducible** |

That split is the same one T8 records (`P-02 static`, `P-05 static`): the car has three rotating
weapon systems (turret, arm, pods) and two translating ones (recoil, bay slides) that JC3 cannot
express.

## 5. What the build has today

`Working/Parts/bm_vehicle_parts.json` (B-04): the parts manifest gives the turret/cannon/Vulcan/
missile pods behaviour rows, with these recorded limits:

* `rotating_parts[]` rows are written from T-12 rows with `behaviour_channel: rotating`;
  `batmobile_jet` is **omitted** ("its bones translate and no rotation is animated", so no
  `rotation_axis` source);
* `door_parts[]` = **[25]** only (the canopy/`Hood` row);
* `aim_part_constraints[]` = **0 rows** (all 85 fleet rows are suspension; the tanks have none);
* `hinged_parts[]` has an **omission for P-13** (`SteeringWheel`, `part: null`).

So as built, the **missile pods (P-07/P-08) and the riot-suppressor arm (P-04) carry the `door`
channel but no `part`** — like the canopy, the geometry still lives in the pod shell, and no
`door_parts[]`/`hinged_parts[]` row can reference it. Adding a bay hinge means a B-02 face-level
re-cut first (the same gap the canopy has; see `doors-canopy-trunk-plan.md` §6).

## 6. The values, as one list

```
missile hatch hinge : axis (0,0,±1)   limits 0..15 deg   open 0.833 s  close 0.833 s
missile pod angles  : T/B 14.988 deg   Mid slide 10.866 cm (lost)
mine cover hinge    : 0..65 deg        inside the 2.000 s spread
riot arm hinge      : 0..124 deg       2.000 s open / 2.000 s close
weapon-array slides : 68.508 / 69.783 / 68.122 cm (lost)
turret yaw hinge    : axis +Y   -179..179 deg   spin clip 2.600 s / 60.001 deg, peak 174.05 deg/s
cannon pitch hinge  : axis +X   -5..20 deg      pivot (0, 2.5347, 0)
cannon fire cycle   : 0.700 s   barrels 53.376 / 36.129 cm recoil (lost)
cannon reload       : 0.467 s per side, 79.75 deg shell sweep
Vulcan rotating row : axis +X (joint), 6 blades, rpm_multiplier 1.0, visible -1..-1
Vulcan speed        : 2160 deg / 3.900 s = 92.3 rpm mean, 204.9 rpm peak (weapon_rpm, code-timed)
```

## 7. How to verify

* **Missile bay** (Q-1): fire the pods; pass = the hatch reaches 15° ±0.5 within 0.833 s of the
  fire event, holds open while the pods are out, and is shut 0.833 s after the last launch.
* **Vulcan**: pass = the barrels are turning by the first round and reach the 6-turn/3.9 s rate
  (≈92 rpm) by the second burst; no spin at rest.
* **Cannon**: pass = the pitch hinge stays inside -5…20° while aiming, and the fire cadence matches
  the 0.700 s clip at full auto.
* **Turret**: pass = yaw sweeps the full -179…179° without clipping, and the 60° test sweep takes
  2.6 s ±0.2 s.

## 8. Reproduce

```
python -c "import json,re;d=json.load(open('Research/BatmobileGrab/ANIMATIONS.json'));
[print(s['name'],s['num_frames'],round(s['sequence_length'],3),s['notify_count'],
 [(b['bone'],b['dpos_cm'],b['drot_deg']) for b in s['moved_bones']])
 for s in d['sequences'] if s['package_label']=='Batmobile' and
 re.search(r'Missle|Cannon|ChainGun|Spread|Turret',s['name'])]"
python Tools/scripts/jc3doors.py --check        # door/hatch hinges incl. the 16 MissileHatch rows
python Tools/scripts/jc3parts.py check          # parts/behaviour rows against the donor entity
```

## 9. UNKNOWNs

1. **No duration exists for a JC3 weapon motion.** `all_door_part_properties` has no rate,
   `rotating_parts[]` has rpm but no ramp, and the entity has zero animations — the BmAK seconds
   are acceptance criteria only.
2. **Whether `MissileHatch` works on a `CCar`.** All 16 shipped rows are on the monorail missile
   car (`CTrain`); nothing in that entity opens them either, so the code path is inferred.
3. **Whether `GatlingGun` works on a `CCar`.** 24 parts, 3 chassis, all boat/helicopter.
4. **`rotoscope_rpm_per_cycle`'s meaning** (20.0 on `GatlingGun`) — decoded value, undefined
   semantics (`MOVING_PARTS.md`).
5. **The bay's opening trigger.** BmAK's spread clips have 3 notifies (12/15 on `_Game`); their
   contents are not decoded here, so which event opens the bays in BmAK is UNKNOWN.
6. **Whether a `_partswap` part can be toggled at runtime.** The one shipped example is an authored
   alternate part; no entity shows a transition.
7. **The exact pod hinge pivot and axis.** T8 gives the bones' rotation axis (`[-1,0,0]` in JC3
   space for the left top pod) but the pods are inside the shell with no part pivot; B-02 must cut
   and place it.
