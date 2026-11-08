# T-WP13 — forced extra weapon slots

**Verdict.** The two reference graphs are decoded and listed below. Both carry **exactly two
non-null slot pointers and a shield that is not a slot**: the shield is `CPartProp` parts with the
`BavariumShield` behaviour plus attached effects / a value-driven usage. So the operator's premise
("2 weapons plus a shield") is true as a description of the vehicle, but the files do **not** show a
third weapon slot — neither graph has a fifth pointer or any additional slot member. The ruling is
therefore applied as a **forced** design: the Batmobile entity needs **8 slot members** for the 8
slot-able BmAK weapon objects, built from the only slot vocabulary that exists (the four root
pointers), by repeating the root object. Names and members with no shipped evidence are marked
**UNKNOWN**; no JC3 implementation is invented.

Built from the decoded `.epe` XML cache the repo's own reader uses
(`Tools/scripts/jc3wiring.py`, `parse_epe`). Nothing was launched, attached to or injected into a
game process.

## 0. Change record (per `AGENTS.md`)

| item | value |
|---|---|
| intended change | add one report; no existing repo file is edited |
| file | `tmp/freebuff/reports/wp13-slots-force.md` (new) |
| why this file | the operator's card names this path as the deliverable (`tmp/freebuff/running/L1__8012-wp13-slots.txt`, `DONE:`) |
| revert | delete the file; nothing else changes |

Read-only inputs, no build file written.

## 1. Inputs and identity

| input | identity | use |
|---|---|---|
| `E:/Modding/_gamedata/JC3grab/wiring/epe/v0202_car_capstone_bavariumtank_military_01.ee.xml` | sha256 `1c52a09e29d0818df46831573ed4985c24db9bbe4100b89304e28d63a5f4d86f` | graph A (Imperator Bavarium Tank) |
| `E:/Modding/_gamedata/JC3grab/wiring/epe/v2601_helicopter_urga_heavyassault_military_01.ee.xml` | sha256 `94094d48d23884d4290e1c2556e03c3807a9c6e2792a7be74df02c951a58ee30` | graph B (Urga Mstitel) |
| `Builds/bm-RC2/aaf/editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/v0300_car_kensington_sportsmuscle_debug.epe` | sha256 `2db78866360b960dfb30183740bf14b80fafa048828610a06ab2dd0d91432b8b` | the current Batmobile build graph |
| `Research/JC3Grab/WEAPON_WIRING.jsonl` / `.md` | decoded rows for all 53 armed entities | slot model, per-entity slots and points |
| `Research/JC3Grab/PARTS_TABLE.jsonl` | decoded part behaviour | `BavariumShield` parts |
| `Research/BatmobileGrab/WEAPONS.md` | G1-08 record | the BmAK weapon object list |
| `Research/BatmobileGrab/SOCKETS_JC3.md` | G1-13 record | the 65 BmAK sockets / muzzle anchors |
| `Builds/bm-RC2/verify/weapon_points_vs_bmak.md` | B-05/G2 record | the build's 9 `SWeaponPoint`s |
| `E:/Modding/_gamedata/JC3grab/strings_rt/rt.xml` | shipped `.stringlookup` (decoded text) | display-name → graph mapping |

### Name → graph mapping (read, then matched)

The shipped localisation names the two vehicles and describes their armament:

- `rt.xml:82882` — "The **Imperator** assault tank is equipped with a powerful Bavarium shield that
  is capable of deflecting most ballistic and explosive weaponry."
- `rt.xml:82934` — "The intimidating **URGA Mstitel** is equipped with **four precision rocket
  launchers and a heavy machine gun**."

The string table is hash-keyed, so it does not carry the entity path. The mapping below is by
armament, not by name:

| vehicle | graph | why this graph |
|---|---|---|
| Imperator Bavarium Tank | `v0202_car_capstone_bavariumtank` | the only Bavarium tank chassis; 2 weapons + 3 `bavariumtank_shield_*` parts + `BavariumShieldOn` |
| Urga Mstitel | `v2601_helicopter_urga_heavyassault` | the only Urga graph with **four** rocket points (`w606` `internal_fire_position_1..4`) **and** a heavy MG (`w607`) **and** a `BavariumShield` part (`heavyassault_shield`) |

The Di Ravello personal chopper described at `rt.xml:82935` ("four precision rocket launchers, a
machine gun, and Bavarium shield technology") is the separate graph
`v2604_helicopter_urga_advancedassault_signature_shielded_di_ravello.ee`; it is not the Mstitel, and
its four rocket points are `fire_position_1..4` type 0 on `w621`.
**UNKNOWN:** an explicit name→path table (the `.stringlookup` keys are hashes). The armament match is
the evidence; a name table would settle it beyond doubt.

## 2. Graph A — Imperator Bavarium Tank (`v0202_car_capstone_bavariumtank_military_01.ee`)

Root: `CCar` `v0202_car_capstone_bavariumtank_military_01`.

### Slot members (all four properties the class carries)

| slot member | property in the `.epe` | value | resolves to |
|---|---|---|---|
| 1st driver | `id:851CAABE` (`main_weapon`) | `14F9CF34=FFFF9704` | `w602_mediumtank_canon` (`CBulletWeaponBase`) |
| 2nd driver | `id:00568A74` (no name recovered) | `004AD766=FFFF4B81` | `w603_mediumtank_mgun` (`CBulletWeaponBase`) |
| 1st gunner | `mounted_weapon` | `00000000` | — |
| 2nd gunner | `id:AC0BC788` (`mounted_weapon_2`) | `00000000` | — |
| trailing | `id:8580BA42` | `00000000` | — |
| trailing | `id:CA86AA17` | `00000000` | — |

### Weapon points

| weapon | point | type | fire_effect | x | y | z |
|---|---|---|---|---|---|---|
| `w602_mediumtank_canon` | `fire_position_0` | 2 | 0 | 0.0 | 0.3739 | -5.8174 |
| `w603_mediumtank_mgun` | `fire_position_0` | 2 | 0 | 0.469 | 0.558 | -1.876 |

Weapon components: `w602` carries `CLightWeaponComponent` `warning_light`; `w603` carries none.

### The shield (not a slot)

| member | class | evidence |
|---|---|---|
| `bavariumtank_shield_body` | `CPartProp` | part index 3, behaviour `BavariumShield` (`PARTS_TABLE.jsonl`) |
| `bavariumtank_shield_turret` | `CPartProp` | part index 36, `BavariumShield` |
| `bavariumtank_shield_cannon` | `CPartProp` | part index 37, `BavariumShield` |
| `BavariumShieldOn` | `SValueDrivenEffectUsage` | named object in the graph |
| `bavarium_shield_bullet_impacts` | `SDynamicAttachedEffect` | named object |
| `bavarium_shield_explosive_impacts` | `SDynamicAttachedEffect` | named object |
| `bavarium_shield_sound` | `SAttachedEffect` | named object |

The same three-part shield appears on the medium tank (`mediumtank_shield_body/turret/cannon`), so it
is a chassis capability, not a weapon.

## 3. Graph B — Urga Mstitel (`v2601_helicopter_urga_heavyassault_military_01.ee`)

Root: `CHelicopter` `v2601_helicopter_urga_heavyassault_military_01`.

### Slot members

| slot member | property in the `.epe` | value | resolves to |
|---|---|---|---|
| 1st driver | `id:851CAABE` (`main_weapon`) | `A68DA2AB=FFFF93D7` | `w607_heavyhelicopter_mgun` (`CBulletWeaponBase`) |
| 2nd driver | `id:00568A74` | `095573A7=FFFF9DD9` | `w606_heavyhelicopter_missile` (`CMissileWeaponBase`) |
| 1st gunner | `mounted_weapon` | `00000000` | — |
| 2nd gunner | `id:AC0BC788` | `00000000` | — |
| trailing | `id:8580BA42` | `00000000` | — |
| trailing | `id:CA86AA17` | `00000000` | — |

### Weapon points

| weapon | point | type | fire_effect | x | y | z |
|---|---|---|---|---|---|---|
| `w607_heavyhelicopter_mgun` | `fire.point1` | 0 | 0 | 2.09 | 0.89 | -2.28 |
| `w607_heavyhelicopter_mgun` | `fire.point2` | 0 | 0 | -2.09 | 0.89 | -2.28 |
| `w606_heavyhelicopter_missile` | `internal_fire_position_1` | 2 | 0 | 0.1639 | 0.2313 | 0.0052 |
| `w606_heavyhelicopter_missile` | `internal_fire_position_2` | 2 | 1 | -0.1455 | 0.2343 | 0.0052 |
| `w606_heavyhelicopter_missile` | `internal_fire_position_3` | 2 | 3 | 0.1646 | -0.0903 | 0.0052 |
| `w606_heavyhelicopter_missile` | `internal_fire_position_4` | 2 | 2 | -0.1505 | -0.0903 | 0.0052 |
| `w606_heavyhelicopter_missile` | `fire.point1` | 0 | 0 | 3.65 | 0.86 | -1.33 |
| `w606_heavyhelicopter_missile` | `fire.point2` | 0 | 0 | -3.65 | 0.86 | -1.33 |

Components: `w607` `CBarrelSpinWeaponComponent` `BarrelSpinWeaponComponent`; `w606`
`CLightWeaponComponent` `warning_light`.

### The shield (not a slot)

| member | class | evidence |
|---|---|---|
| `heavyassault_shield` | `CPartProp` | part index 12, behaviour `BavariumShield` (`PARTS_TABLE.jsonl`) |

## 4. What the two graphs actually prove about slot capacity

| fact | graph A | graph B | fleet (G2-11) |
|---|---|---|---|
| slot properties on the root | 4 | 4 | 4 on every root of all 53 armed entities |
| non-null slot pointers | **2** | **2** | max 2 driver, max 2 gunner; never more than 2 on one root |
| third/fifth pointer | absent | absent | absent in all 232 `.epe` graphs |
| shield | 3 parts + 1 usage + 2 effects + 1 sound | 1 part | `BavariumShield` = 26 parts over 14 entities / 4 chassis |
| shield consumes a slot | **no** | **no** | no |

Both vehicles "ship 2 weapons plus a shield" because the shield is a **part/effect capability**, not a
weapon and not a slot. The operator's conclusion (2 driver slots is a convention, not an engine hard
limit) is compatible with the files; the files simply do not demonstrate a third slot. Forcing one is
a design decision, not a decoded value — recorded as such here.

## 5. The BmAK weapon set the slots must cover

From `Research/BatmobileGrab/WEAPONS.md` (62 objects, 13 classes; 36 gadget objects, 11 gadget
classes). The gadget objects, by whether a slot pointer can bind them:

| # | BmAK object | class | package | slot-able? | why |
|---:|---|---|---|---|---|
| 1 | `Batmobile_Heavy_Cannon_Primary` | `RBatmobileHeavyCannon` | base/MK2/Funhouse | **yes** | fires `ProjectileArchetype` |
| 2 | `Batmobile_Cannon_V2` | `RBatmobileCannon` | base/MK2/Funhouse/Joker | **yes** | chain gun + riot suppressor modes |
| 3 | `Batmobile_Missile_Launcher` | `RBatmobileMissileLauncher` | base/MK2/Funhouse | **yes** | `MissileClass` |
| 4 | `Batmobile_EMP_Missile_Launcher` | `RBatmobileEMPMissile` | base/MK2/Funhouse | **yes** | `ProjectileForCarsArchetype` |
| 5 | `Vehicle_Tracker` | `RBatmobileVehicleTracker` | base/MK2/Funhouse | **yes** (forced) | `RPursuitModeMissileLauncher.ProjectileArchetype`; JC3 has no tracker class (T-WP9) |
| 6 | `Batmobile_JokerHeavy_Cannon` | `RBatmobileHeavyCannon` | Joker | **yes** | `ProjectileArchetype` |
| 7 | `Batmobile_JokerCannon_V2` | `RBatmobileCannon` | Joker | **yes** | bullet weapon |
| 8 | `Batmobile_JokerMissile_Launcher` | `RBatmobileMissileLauncherJoker` | Joker | **yes** | `MissileClass`, `MissileSockets` 10 items |
| 9 | `Batmobile_EMP_Burst` | `RBatmobileEMP` | base/MK2/Funhouse | no | entity-level `CForcePulse`, 307 in fleet (T-WP5) |
| 10 | `Batmobile_Winch` | `RBatmobileWinch` | base/MK2/Funhouse | no | no winch class in the 103-class census (T-WP6) |
| 11 | `Batmobile_Sonar` | `RBatmobileSonar` | base/MK2/Funhouse | no | no sonar class (T-WP8) |
| 12 | `Drone_Hacker` | `RBatmobileAllegianceSwitcher` | base/MK2/Funhouse | no | no allegiance class (T-WP7) |
| 13 | `Batmobile_Booster` | `RBatmobileBooster` | all four | no | nitro is a stat/button (`arcade.nitro_boost`), not a slot (T-WP11) |

**8 slot-able weapon objects; 5 non-slot gadgets.** The Joker objects are a separate vehicle
package, but the card requires every BmAK weapon in both modes on the one Batmobile entity, so they
are counted as required slots here.

## 6. The member set the Batmobile entity needs

The only slot vocabulary that exists is the four root pointers. The build graph today has one root
with `main_weapon` bound (the donor's `w618_sportsmuscle_missile`) and 9 `SWeaponPoint`s
(`Builds/bm-RC2/verify/weapon_points_vs_bmak.md`: 5 named after BmAK sockets, 4 type-4
`attach.vehicle` markers).

### Required slot members (8)

Recommended forced layout: **four `CCar` roots on the one entity, each with its two driver pointers
non-null.** This uses only decoded member names, never mixes driver and gunner pointers on one root,
and has a decoded precedent for more than one root in one entity
(`v4603_plane_urga_cargotransport_military_cargo_tank.ee` carries `CAirPlane` + `CCar`, each with its
own slot set and its own interaction context).

| root | slot member | property | BmAK weapon | weapon point |
|---:|---|---|---|---|
| 1 | 1st driver | `main_weapon` = `id:851CAABE` | `Batmobile_Heavy_Cannon_Primary` | `CannonMuzzle` |
| 1 | 2nd driver | `id:00568A74` | `Batmobile_Cannon_V2` (chain gun); riot mode fires from `RiotSuppressorMuzzle` | `ChainGunMuzzle` |
| 2 | 1st driver | `main_weapon` = `id:851CAABE` | `Batmobile_Missile_Launcher` | `MissileL`, `MissileR` + 2 more (missile count UNKNOWN) |
| 2 | 2nd driver | `id:00568A74` | `Batmobile_EMP_Missile_Launcher` | `MissileL`, `MissileR` (array 2 items, mapping inferred) |
| 3 | 1st driver | `main_weapon` = `id:851CAABE` | `Vehicle_Tracker` | `BattleModeSpotLight` |
| 3 | 2nd driver | `id:00568A74` | `Batmobile_JokerHeavy_Cannon` | UNKNOWN (no Joker socket decoded) |
| 4 | 1st driver | `main_weapon` = `id:851CAABE` | `Batmobile_JokerCannon_V2` | UNKNOWN |
| 4 | 2nd driver | `id:00568A74` | `Batmobile_JokerMissile_Launcher` | UNKNOWN |

Alternative if a single root must fire everything: one root with all four pointers non-null
(`main_weapon`, `id:00568A74`, `mounted_weapon`, `mounted_weapon_2`) plus a second such root. That is
shorter but has **no decoded precedent** — G2-11 found no entity mixing driver and gunner slots.

### Required non-slot members (5, one per gadget)

These cannot take a slot; each needs its own entity object/class, and four have no JC3 carrier at all:

| BmAK gadget | member it needs | carrier |
|---|---|---|
| `Batmobile_EMP_Burst` | `CForcePulse` (entity object) | decoded class, 307 in fleet; firing trigger UNKNOWN |
| `Batmobile_Booster` | nitro stat block (`arcade.nitro_boost`) | decoded, 145 vehicles |
| `Batmobile_Winch` | winch/rope module | **none** in the 103-class census |
| `Batmobile_Sonar` | sonar class | **none** |
| `Drone_Hacker` | allegiance-switch class | **none** |

### Weapon points: what the entity needs vs what it has

| BmAK point role | socket (G1-13, metres) | build has it? |
|---|---|---|
| heavy cannon | `CannonMuzzle` 0.0003, 1.7025, -0.4559 | yes |
| chain gun | `ChainGunMuzzle` -0.4074, 1.5519, -0.1669 | yes |
| riot suppressor | `RiotSuppressorMuzzle` 0.389, 1.451, 0.142 | **no** (socket exists, no point) |
| missile tubes | `MissileL` 0.594, 1.485, -1.147 / `MissileR` -0.589, 1.490, -1.147 | yes, 2 of them; BmAK's launcher wants more (array payload not decoded) |
| tracker (scan missile) | `BattleModeSpotLight` 0.0004, 1.8346, -0.0664 | yes |
| Joker cannon / Joker launcher | — | **no**, and no Joker socket coordinate is decoded |

So the entity needs at least **8 firing points**; it has 5 socket-named ones today (the other 4 are
`attach.vehicle` markers and are not muzzles). Missing: the riot muzzle point and points for the
Joker weapons, plus however many extra missile tubes BmAK's `MissileSockets` array turns out to
name — **UNKNOWN**, payload not decoded (`WEAPONS.md` §5: `MissileSockets` 10 items × 8 B on the
Joker launcher, `MissileLaunchSockets` 2 items × 8 B on the EMP launcher).

## 7. UNKNOWN (not readable from the files)

1. **A third slot member.** No graph in the 232 decoded entities carries a fifth pointer or any
   property whose Jenkins hash resolves to a weapon-slot word beyond `main_weapon` /
   `mounted_weapon_2`. Any forced name (`main_weapon_2`, `weapon_slot_3`, …) has **no** shipped hash
   in the name tables; how a forced property is serialised and whether the class reads it is
   UNKNOWN.
2. **Whether two roots on one car chassis fire from the driver seat.** The only multi-root precedent
   is a tank inside a cargo plane, with its own interaction context and seats. The Batmobile case is
   a different arrangement; behaviour is UNKNOWN without a process test (test ban).
3. **The `id:00568A74` name.** It resisted the 1.1-million-string search; its id is the name of
   record.
4. **Joker weapon points.** The Batmobile_V2 socket list (65) is from the base package; no Joker
   socket coordinates are decoded.
5. **Missile array → socket mapping and tube count.** Payloads not decoded; `MissileL`/`MissileR` are
   matched by name/shape.
6. **Name→path table** for "Imperator Bavarium Tank" and "URGA Mstitel" — matched by armament, not by
   a decoded key table (§1).
7. **Runtime firing of the forced slots.** Nothing in the entity says which input fires which slot
   (G2-11 §6); with forced slots this is even less constrained.

## 8. Checks

| check | result |
|---|---|
| both reference graphs decoded with the repo reader (`jc3wiring.parse_epe`) | PASS |
| graph A: 4 slot properties, 2 non-null, 2 weapons, 2 points | PASS |
| graph B: 4 slot properties, 2 non-null, 2 weapons, 8 points | PASS |
| shield parts resolve to `BavariumShield` in `PARTS_TABLE.jsonl` | PASS (A: 3 parts; B: 1 part) |
| BmAK gadget objects enumerated from `WEAPONS.md` | PASS (13 objects / 11 classes) |
| 8 slot-able + 5 non-slot = 13, no object counted twice | PASS |
| build point inventory read from `Builds/bm-RC2/verify/weapon_points_vs_bmak.md` | PASS (9 points: 5 socket + 4 attach) |
| forced members that use only decoded property names | 8/8 (four roots × `main_weapon` + `id:00568A74`) |
| invented property names used | 0 |
| game process started / attached / injected | none |

### Reproduce

```bash
cd Tools/scripts && python - <<'PY'
import sys, os; sys.path.insert(0, '.')
import jc3wiring as W
CACHE = r"E:/Modding/_gamedata/JC3grab/wiring/epe"
for f in ("v0202_car_capstone_bavariumtank_military_01.ee.xml",
          "v2601_helicopter_urga_heavyassault_military_01.ee.xml"):
    objs = W.parse_epe(os.path.join(CACHE, f))
    byid = {o.oid: o for o in objs if o.oid}
    for r in [o for o in objs if o.cls in W.ROOT_CLASSES]:
        print(f, r.cls, [(lbl, r.get(p), (byid.get(r.get(p)).name if r.get(p) in byid else None))
                         for lbl, p, _w in W.SLOTS])
    for o in objs:
        if o.cls in W.WEAPON_CLASSES:
            print("  ", o.name, [(c.name, c.get("type"), W.xyz(c.get("world")))
                                 for c in o.children if c.cls == "SWeaponPoint"])
PY
```

## 9. Sources

| source | location |
|---|---|
| slot model, 2-slot maximum | `Research/JC3Grab/WEAPON_WIRING.md` §1–§2; `WEAPON_WIRING.jsonl` |
| fleet numbers (53 armed, 232 graphs, `BavariumShield` 26 parts / 14 entities / 4 chassis) | `Research/JC3Grab/FEATURE_CENSUS.md`, `ENTITIES.md`, `PARTS_TABLE.jsonl` |
| BmAK gadget objects, classes, socket arrays | `Research/BatmobileGrab/WEAPONS.md` (§2, §5, §6–§16) |
| BmAK sockets and muzzle anchors | `Research/BatmobileGrab/SOCKETS_JC3.md` |
| build's 9 points | `Builds/bm-RC2/verify/weapon_points_vs_bmak.md` |
| T-WP13 blocked row and the operator's decision | `Working/Translation/T7_WEAPONS.md` §2; `Working/Translation/DECISIONS_NEEDED.md:205` |
| vehicle names and armament text | `E:/Modding/_gamedata/JC3grab/strings_rt/rt.xml:82882, 82934` |
