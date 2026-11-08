# Build B-05 — the entity graph (`Builds/bm-RC4-entity`)

**Status: done for the decoded rows; every invented-value risk is named below.** Built by
`Tools/scripts/bm_entity.py --write` from **`Builds/bm-RC4-parts`** (B-04) into
**`Builds/bm-RC4-entity`**, with `ConvertProperty` round trip, `bm_entity.py --check` and the
name-hash census all green. No game was launched, nothing was installed, no shipped file was edited.

## 0. Change record (AGENTS.md)

| item | value |
|---|---|
| intended change | rebase B-05 onto the RC4 chain and add the rows the apply-* reports decided: T-WP13's forced slot space, the T-WP4 split references, the EMP/sonar pulses and the winch anchor |
| file edited | `Tools/scripts/bm_entity.py` (the generator; the build tree is its output) |
| why this file | it is the card's own B-05 generator, and `GRAB_BACKLOG.md` §8 B-05 names `Working/Entity/bm_epe_edits.json` + the `.epe` in the build as its out |
| revert | `Tools/` is **untracked in git**, and no pre-edit backup of the script exists. The edits are confined to: the constants block (`BASE_TAG`, `TAG`, new `SLOT_PROPS`/`ROOTS`/donor paths), the `WEAPONS` rows (`root`, `private_tune`), three new helpers (`name_hash_mismatch`, `winch_origin`, `forced_roots`, `gadgets`), the `plan()` slot-binding move, and the `check()` census. Restore `BASE_TAG="bm-009"`/`TAG="bm-005"` and delete the helpers + their `plan()` calls to return to the bm-005 generator. Delete `Builds/bm-RC4-entity/` to remove the build itself |

## 1. What was built

| item | value |
|---|---|
| base | `Builds/bm-RC4-parts` (RC4 chain: `test-091` → `bm-RC4-base` → `bm-RC4-parts`) |
| output | `Builds/bm-RC4-entity/aaf/.../v0300_car_kensington_sportsmuscle_civilian_01.epe` |
| size / sha256 | 133,896 B / `b0a8b5a988c5bc21f37aca61a985ca9d298d9c6874cbd66fc4d6e717e14da323` |
| generated spec | `Working/Entity/bm_epe_edits.json` (37 planned rows, 22 edits, 69 skipped, 15 declared) |
| receipt / installer | `Builds/bm-RC4-entity/receipt.json`, `install.ps1` (`Install/Verify/Rollback091/Status`) |
| edits applied | 4 weapon components + 9 points, 10 T-18 custom lights, 15 interaction transforms, 4 CCar roots (8 slot members), 2 gadget pulses, 1 winch anchor |

The base graph was re-derived, not assumed: `bm_entity.py` exports the base `.epe` and stops if its
census moves. Measured base root: `health` 100, `invulnerable` 0, `damage` **670155287**
(`bm-RC4-parts`' own hash — the old `bm-009` value 1928726201 is not in this lineage, so the
preserve list is now read from the base graph, not typed). `bat_base.ctune` occurs exactly once.

## 2. Object and class counts, before → after

| | base (`bm-RC4-parts`) | built (`bm-RC4-entity`) |
|---|---:|---:|
| objects (all, incl. the classless `root` wrapper) | **416** | **477** |
| classed objects | 415 | 476 |
| classes | **43** | **47** |
| `CCar` roots | 1 | 4 |
| `CBulletWeaponBase` components | 0 | 4 |
| `SWeaponPoint`s | 0 | 9 (5 muzzles + 4 `attach.vehicle`) |
| `SVehicleLight`s | 22 | 32 (10 T-18 custom) |
| `CForcePulse` | 1 | 3 |
| `CVehicleCargoBay` | 0 | 1 |

The graph diff is **+61 objects** (37 planned rows; a cloned weapon component drags its
`SEffects`/5 effects/`CAIEntityProxy` children in, which is why the row count is lower than the
object count). `--check`'s Done 3 is `416 + 61 = 477`. New classes (4): `CBulletWeaponBase`,
`SWeaponPoint`, `CAIEntityProxy`, `CVehicleCargoBay`.

## 3. The 8 forced slots (T-WP13)

Four `CCar` roots on the one entity, each carrying all four root pointers; the **slot space is
4 × (`main_weapon` + `id:00568A74`) = 8 members**. Only decoded member names and ids are used.

| root | `main_weapon` (`id:851CAABE`) | `id:00568A74` | BmAK object |
|---|---|---|---|
| `…_civilian_01` (donor root) | `w602_mediumtank_canon` | `w603_mediumtank_mgun` | Heavy Cannon Primary / Cannon V2 |
| `…_civilian_01_slot2` | `w618_sportsmuscle_missile` | `w618_sportsmuscle_missile_emp` | Missile Launcher / EMP Launcher |
| `…_civilian_01_slot3` | **null (reserved)** | **null (reserved)** | Vehicle_Tracker / Joker heavy cannon |
| `…_civilian_01_slot4` | **null (reserved)** | **null (reserved)** | Joker V2 cannon / Joker missile launcher |

**4 bound, 4 reserved.** The four remaining slot-able BmAK objects have **no T-11 carrier** and the
Joker weapons have **no decoded socket**, so their pointers stay `00000000` rather than naming a
weapon object that does not exist. The four gunner pointers (`mounted_weapon`, `id:AC0BC788`) and
the two trailing pointers (`id:8580BA42`, `id:CA86AA17`) are null on all four roots — no shipped
graph mixes driver and gunner slots.

The three extra roots are cloned from the donor root's **members only** (no children). Cloning the
children would duplicate the interaction context, the light list and the effect set. Each gets a
fresh `_object_id` and a name whose `name_hash` is `hash_jenkins(name)` (0 mismatches, §8).

## 4. The 5 gadgets outside the slot space

T-WP13 counts five non-slot gadgets. Three have a carrier in this graph; two do not and are
declared, not invented.

| # | gadget | object written | detail |
|---:|---|---|---|
| 1 | `Batmobile_EMP_Burst` (T-WP5/B-18) | **`CForcePulse_EMP`** | cloned from the EMP truck's own `EMP` pulse: `truck_emp.ftune`, flag triple `4912FC04` 0 / `AE6F7EFF` 1 / `CF4F7880` 1 (unique in 307 pulses), world = graph origin |
| 2 | `Batmobile_Booster` (T-WP11) | **none** | it is the module member `arcade.nitro_boost` (B-24 owns it), not an entity object |
| 3 | `Batmobile_Winch` (T-WP6/B-16) | **`WinchAnchor`** | `CVehicleCargoBay` clone, §6 |
| 4 | `Batmobile_Sonar` (T-WP8/B-20) | **`CForcePulse_Sonar`** | clone of the graph's own pulse with `gen_explosion_5m_nodamage.ftune` (0 damage / 5 m) |
| 5 | `Drone_Hacker` (T-WP7/B-19) | **none** | needs an `SAttachedEffect` whose effect is a private `.effc` plus a usage the engine dispatches on; neither exists |

The booster's and hacker's absence is recorded in the spec's `declared[]`, and the report counts
them as **0 of the 61 added objects each**.

## 5. T-WP4 — the split, entity side

The EMP launcher clone (`w618_sportsmuscle_missile_emp`) is the only component whose tune members
are repointed:

| member | value written | owner |
|---|---|---|
| `id:AA7096C9` (`tuning_file`) | `editor/entities/jc_weapons/06_vehicle/w618_batmobile_emp/w618_batmobile_emp.wtune` | B-06 authors the five w143 guidance values there (`missile_turning_speed` 300, random 60, acceleration 30→65 over 0.2→10 s, random 2→5) |
| `id:6D4C8277` (`autoaim_tuning_file`) | `.../w618_batmobile_emp/autoaim_batmobile_lockon.wtune` | B-06 authors the new lock-on `AutoAim`: w143's 0.12 / 0.15 cone, `MaxAimDistance` 120, `CanTargetCharacters` 0, `CanTargetVehicles` 1, `CanTargetRigidObjects` 1 |

Guidance and cone are **tune members**, so they are B-06's write; the entity's share is these two
path references plus the single `CForcePulse_EMP` (written once, not once per root). The disable
half (T-WP4b/T-WP15) has no member and stays a named omission.

## 6. Winch anchor (B-16)

`WinchAnchor` is a clone of the cargo plane's `CVehicleCargoBay` (`v4603_plane_…_blackhand_01`),
members measured, children **not** cloned (the plane's `CShapeTrigger` is its hold volume, not the
Batmobile's). `enabled` 1, `enable`/`disable` empty (as on all 12 shipped bays), and:

```
world = 1,0,0,0, 0,1,0,0, 0,0,1,0, 2.865541,0,0.5899999,1
```

which is `SOCKETS_JC3.json` → `WinchOrigin` → `relative_location_cm` (286.554138, 0, 58.999992) / 100,
translation only (rotation null/identity in the socket record). `--check` compares the matrix to
that socket at 1e-4 m — PASS.

## 7. B-12 precondition 3 and B-26

* **B-12 / mode switch:** no object is written. Precondition 3 (a runtime entity swap) is
  **UNKNOWN** — `mode-switch-carriers.md` §7 **U1**: no data selects a variant at runtime, and the
  `JustCause3.exe` streaming consumer is not decoded. The spec's `declared[]` names it. The two
  variant `.epe`s and the `BattleMode` usage remain B-12's work.
* **B-26 / per-entity audio override:** **0 objects in this build**. The 21 of 45 pinned GUIDs are
  fired by code from shared `effects`/`character` banks; the override needs a private
  effects-class bank, per-entity binding rows and two recorded takes, which is the card's own gate
  (and a test that is banned). It is counted as `audio_override_objects: 0` in the receipt.

## 8. Plan stand-ins — every `unbound` and `UNKNOWN` object

`unbound` weapon components: **0** (all four are bound to a non-null slot; `--check` fails on any
unbound component). Every remaining stand-in is listed here:

| stand-in | count | why it is UNKNOWN / not final |
|---|---:|---|
| extra `CCar` roots `_slot2/_slot3/_slot4` | 3 objects | forced T-WP13 design. A childless extra root has **no shipped precedent** (the cargo-plane entity's second root is a whole tank), and **whether several roots on one car chassis fire from the driver seat is UNKNOWN** (no entity states the input→root binding). All four roots also share the donor's `interaction_context` pointer |
| reserved slot pointers (roots 3/4) | 4 members | null: Vehicle_Tracker + 3 Joker weapons have no T-11 carrier; no Joker socket coordinate is decoded |
| `w602_mediumtank_canon` tune/autoaim | 1 object | still names the APC template's `w206_mounted_capstone_m2hm.wtune` + `autoaim_assault_rifle.wtune`, because the copy keeps the template's unnamed members. **B-06** repoints it at the private w602 copy |
| `w603_mediumtank_mgun` tune/autoaim | 1 object | same (APC template paths) — B-06 |
| `w618_sportsmuscle_missile` tune/autoaim | 1 object | same (APC template paths); the plain missile's lock-on tune is B-06's |
| `w618_sportsmuscle_missile_emp` private files | 1 object | the two paths point at files **B-06 has not created yet**; until then the reference is a plan path, not a shipped asset |
| `CForcePulse_EMP` material table | 1 member | `id:D3DDD766` zeroed: the truck's `emp_flatbed_table` is an opaque `CMaterialEffectTable`, not copied |
| `CForcePulse_EMP` / `CForcePulse_Sonar` placement | 2 objects | both sit at the **graph origin**; the Batmobile chassis-centre offset is UNKNOWN (the truck's (0, 2.0356, 0.6992) belongs to the truck's frame and was not transplanted). **Nothing in the decoded files fires either pulse** (G2-17: 14 unowned pulses) |
| `WinchAnchor` | 1 object | enable/disable empty, no pull loop (no length/force/reel/release member in JC3); the drum is a B-04 part and the two BmAK rope components have no JC3 class |
| the 10 T-18 custom lights | 10 objects | each clone inherits `Front_Left_Point`'s 11 positional `id:*` slots, so all ten sit at that lamp; the module anchor is B-07's |
| interaction objects with no named `world` | 69 skipped | the transform sits in an unnamed mat slot (member hash only) — UNKNOWN, not written; the 15 point/trigger transforms that do have a named `world` member are written from the grab (T-13R), so they are not stand-ins |

## 9. Checks run

```
$ python Tools/scripts/bm_entity.py --write
wrote Builds/bm-RC4-entity/aaf/.../v0300_car_kensington_sportsmuscle_civilian_01.epe:
37 planned row(s) = 61 object(s), 22 edit(s), 69 skipped; objects 416 -> 477
  weapons 4, light customs 10, interactions 15, CPartProp added 0                     exit=0

$ python Tools/scripts/bm_entity.py --check
PASS: 4 weapon component(s), 0 unbound, 9 weapon point(s), 32 light(s) (10 T-18 custom),
19/19 part name(s) in the module, 0 dangling | 4 CCar roots, 8 slot members (4 bound,
4 reserved) | 3 gadget object(s) of 5 gadgets | name-hash mismatches 0 (base 0) |
objects 416 + 61 = 477 (476 classed + 1 classless root, 47 classes) | round trip identical
(count definitional; plan equality enforced above)                                     exit=0
```

Independent `ConvertProperty` round trip of the built `.epe` (not the check's copy):

```
--e -> -i -> --e:   .epe sha256 equal True,  XML bytes equal True
built sha256 = b0a8b5a988c5bc21f37aca61a985ca9d298d9c6874cbd66fc4d6e717e14da323
```

The check also enforces, for the built graph: 4 roots with 8 slot members, 4 bound and every bound
pointer resolving to a weapon object; the 3 gadget objects present; `WinchAnchor.world` within
1e-4 m of `WinchOrigin`; `health`/`invulnerable`/`damage` equal to the **base graph's** values;
`bat_base.ctune` exactly once; 19/19 B-04 part names present in the parts module bytes; and a
semantic object-for-object equality between the built graph and the re-derived plan.

## 10. Limits (stated, not papered over)

1. **Nothing was fired.** These are file facts: the slot layout, the tune references, the pulse
   classes and the anchor transform. Whether the engine fires 4 roots, honours the forced second
   driver pointer, or accepts B-06's private tunes is UNKNOWN (test ban).
2. **The root clone is a design, not a decoded pattern.** No shipped entity carries four roots on
   one car chassis; the only multi-root precedent is a tank inside a cargo plane.
3. **B-06 is a dependency of the reference, not of the build.** The `.epe` names two private paths
   that do not exist yet; B-06 must create them or the EMP launcher will resolve nothing.
4. **The light count moved** because `t14_lights.json` now carries 10 custom targets (6 in the
   bm-005 round); the build derives them, it does not pin a number.
5. **B-12/B-26 contribute no object** here for the reasons in §7 — they are not silently dropped.

## 11. Files written and how to revert

| file | change | revert |
|---|---|---|
| `Tools/scripts/bm_entity.py` | rebased to `bm-RC4-parts`/`bm-RC4-entity`; +T-WP13 roots, gadget pulses, winch anchor, base-derived preserve list, name-hash/slot/gadget checks | see §0 (untracked; no backup) |
| `Working/Entity/bm_epe_edits.json` | **regenerated** (37 rows, 22 edits, 69 skipped, 15 declared) | re-run the generator from the reverted script |
| `Builds/bm-RC4-entity/aaf/.../*.epe`, `install.ps1`, `receipt.json` | new build tree (61 objects added) | `rm -rf Builds/bm-RC4-entity` |
| `tmp/freebuff/reports/build-d05-entity-graph.md` | this report | delete |

No game install, dropzone, bank or shipped archive was touched; `installed: false` in the receipt.
