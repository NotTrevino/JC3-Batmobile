# Repeated slot pointers — what shipped graphs actually do (T-WP13 evidence)

**Question.** `tmp/freebuff/reports/wp13-slots-force.md` proposes **8 slot members** for the Batmobile
by repeating the four root slot pointers, because no shipped graph has more than two non-null slots.
A forced design needs evidence that the engine accepts it. This report tests each element of that
design against every armed entity in `Research/JC3Grab/WEAPON_WIRING.jsonl` (53 entities), including
the Bavarium Tank and the Urga Mstitel, and separates what is **shown in a shipped graph** from what
is **not**.

**Headline.** One element of the forced design *is* shipped: **two slots bound to two separate
weapon objects of the same weapon asset** — the heavy patrol boat, 5 variants, gunner pointers
`mounted_weapon` + `mounted_weapon_2`, each pointing at its own `w206_mounted_capstone_m2hm` object
with its own mount parts and its own ±75° turret hinges. That proves the engine runs a duplicated
weapon on two slots, which is the core of the "repeat the pointer" idea. It does **not** prove the
rest: no graph has **3+ non-null slots on one root**, **one weapon object referenced by two slots**,
a **shared slot object id**, a **non-null trailing pointer**, a **driver+gunner mix on one root**, or
**two roots in one entity that both carry weapons**. Those stay UNKNOWN and are listed with the
in-game check that would settle each.

Built read-only from the decoded entity graph (`Tools/scripts/jc3wiring.py` / `parse_epe`, the
reader behind `WEAPON_WIRING.jsonl`). No game was launched, attached to or injected into.

## 0. Change record (per `AGENTS.md`)

| item | value |
|---|---|
| intended change | add one report; no existing repo file is edited, no build file written |
| file | `tmp/freebuff/reports/repeated-slot-pointer-evidence.md` (new) |
| why this file | the operator's card names this path as the deliverable |
| revert | delete the file; nothing else changes |

## 1. Corpus and method

| input | rows / meaning |
|---|---|
| `Research/JC3Grab/WEAPON_WIRING.jsonl` | **53** armed entities, one JSON row each: `roots[]` (name, class, `slots{}`, `other_pointers{}`), `weapons[]` (name, `object_id`, `binding[]`, `points[]`, `mount_parts[]`), `counts` |
| `Research/JC3Grab/WEAPON_WIRING.md` §1–§2 | the slot model, the recovered hashes, the "no switching" finding |
| `Research/JC3Grab/TURRET_LIMITS.md` | the physical hinges each mount actually has |
| `tmp/freebuff/reports/wp13-slots-force.md` | the forced design under test |

Derivation used for every table below: for each root, collect the slot properties whose pointer is
non-null; group them by their **target name**; then ask (a) how many non-null slots, (b) whether any
two slots share a target **name**, (c) whether any two slots share a target **object id**, (d) whether
any slot id repeats on a root. Weapon objects are counted from `weapons[]` and matched to slots by
`binding`.

### Slot-population histogram (all 53 entities, per root)

| non-null slots on the root | entities |
|---:|---:|
| 0 | 1 |
| 1 | 23 |
| 2 | 29 |
| 3+ | **0** |

### The only two slot pairs that occur

| non-null pair | roots | entities |
|---|---:|---|
| `main_weapon` + `secondary (id:00568A74)` (driver pair) | 24 | 24 |
| `mounted_weapon` + `mounted_weapon_2` (gunner pair) | 5 | 5 |

No root mixes a driver pointer with a gunner pointer (`main_weapon` + `mounted_weapon*`: **0**).
The four slot properties are `id:851CAABE` = `main_weapon`, `id:00568A74` (no name recovered),
`mounted_weapon`, `id:AC0BC788` = `mounted_weapon_2`; two trailing pointers (`id:8580BA42`,
`id:CA86AA17`) are null on all 53 (`WEAPON_WIRING.md` §1).

## 2. Case A — the repeated target: heavy patrol boat (the one shipped precedent)

`v1200_boat_capstone_heavypatrol`, **5 variants**, root class `CBoat`. Both gunner pointers are
non-null and both resolve to a weapon called `w206_mounted_capstone_m2hm` — but the **object ids
differ**, so these are two separate weapon objects with the same name, not one shared object.

| variant | `mounted_weapon` slot object | `mounted_weapon_2` slot object | same object? |
|---|---|---|---|
| `..._generated` (debug) | `10FA0585=FFFFDCA7` | `29A43A52=FFFF2C64` | no |
| `..._military_01` | `0AE28EF7=FFFF5CA9` | `57066CCC=FFFF2CB8` | no |
| `..._military_01_delivery` | `F444376E=FFFF245C` | `D9A6337F=FFFFBADA` | no |
| `..._rebel_01` | `44CF96EE=FFFF0CE7` | `3A543DC9=FFFFFB15` | no |
| `..._rebel_01_mm210` | `0CFEADB0=FFFFC14F` | `042E107B=FFFF644D` | no |

Both objects carry their **own** graphite as separate components:

| slot | weapon | fire points | mount parts |
|---|---|---|---|
| `mounted_weapon` | `w206_mounted_capstone_m2hm` | 4: `FirePosition`, `LeftHandMountedAttach`, `RightHandMountedAttach`, `MountAttach` | `heavypatrol_weapon_mount_r_horizontal`, `heavypatrol_weapon_mount_r_vertical` |
| `mounted_weapon_2` | `w206_mounted_capstone_m2hm` | 4: `FirePosition`, `MountAttach`, `LeftHandMountedAttach`, `RightHandMountedAttach` | `heavypatrol_weapon_mount_l_horizontal`, `heavypatrol_weapon_mount_l_vertical` |

And the chassis gives each slot its own hinge (`TURRET_LIMITS.md`, `heavypatrol` `two_cannon` rows):

| slot | part | axis | pivot (x, y, z) | yaw span |
|---|---|---|---|---|
| `mounted_weapon` | `heavypatrol_weapon_mount_r_horizontal` | yaw | `2.7544, 2.7423, -0.2488` | −75 … +75 (150°) |
| `mounted_weapon` | `heavypatrol_weapon_mount_r_vertical` | pitch | `2.7844, 2.9224, -0.2488` | — |
| `mounted_weapon_2` | `heavypatrol_weapon_mount_l_horizontal` | yaw | `-2.7544, 2.7423, -0.2488` | −75 … +75 (150°) |
| `mounted_weapon_2` | `heavypatrol_weapon_mount_l_vertical` | pitch | `-2.7851, 2.9218, -0.2488` | — |

**Distinct or shared?** Distinct objects, distinct aim units, identical asset name. This is the only
shipped example of a duplicated weapon bound to two slots, and it is on the **gunner** pair, on a
**boat**, with **two** slots — not eight, not on driver pointers, not on a car.

**Weapon-selection treatment (what the data says).** None of the boat's data names a selector entry:
`WEAPON_WIRING.md` §2(b) — there is no active-slot index, no next/previous-weapon action and no
weapon group anywhere in the `.epe`; "both slots are simply available". Which key fires each is not
encoded. So the file-level answer to "how the UI treats them" is: **it does not say**; the only
thing the files show is that the two slots are independent mounts with independent aim limits,
which is consistent with them being two separate weapons rather than one merged entry.

## 3. Case B — Imperator Bavarium Tank (`v0202_car_capstone_bavariumtank_military_01.ee`)

| slot | object | target | points |
|---|---|---|---:|
| `main_weapon` (`851CAABE`) | `14F9CF34=FFFF9704` | `w602_mediumtank_canon` | 1 (`fire_position_0`) |
| `secondary (id:00568A74)` | `004AD766=FFFF4B81` | `w603_mediumtank_mgun` | 1 (`fire_position_0`) |
| `mounted_weapon` / `mounted_weapon_2` | `00000000` | — | — |

Distinct objects, distinct names, no repetition, 2 non-null. The shield is parts
(`bavariumtank_shield_body/turret/cannon`, behaviour `BavariumShield`) plus `BavariumShieldOn`,
`bavarium_shield_*` effects — **not** a slot, so the tank is a 2-slot graph, as `wp13` already
states.

## 4. Case C — Urga Mstitel (`v2601_helicopter_urga_heavyassault_military_01.ee`)

| slot | object | target | points |
|---|---|---|---:|
| `main_weapon` | `A68DA2AB=FFFF93D7` | `w607_heavyhelicopter_mgun` | 2 (`fire.point1`, `fire.point2`) |
| `secondary (id:00568A74)` | `095573A7=FFFF9DD9` | `w606_heavyhelicopter_missile` | 6 (`internal_fire_position_1..4`, `fire.point1`, `fire.point2`) |
| `mounted_weapon` / `mounted_weapon_2` | `00000000` | — | — |

Distinct objects, 2 non-null, no repetition. Its eight points all hang off **two** components — the
"four rocket launchers + MG" armament is points, not slots. This is the strongest shipped counter to
reading slot count as weapon count.

## 5. Case D — aircraft with more than two guns on different points

**No aircraft entity has more than two bound weapons** (fleet max is 2 for every class). What the
aircraft do have is many fire points under those two slots:

| entity | bound slots | weapons (points) | bound points |
|---|---|---|---:|
| `v2604_helicopter_urga_advancedassault_*` (5 variants) | `main_weapon`, `secondary` | `w622` (3), `w621` (8) | **11** |
| `v4202_plane_capstone_fighterjet_*` (3) | `main_weapon`, `secondary` | `w610` (1), `w609` (8); `w608` (2) unbound | 9 |
| `v2200_helicopter_capstone_assault_*` (3) | `main_weapon`, `secondary` | `w601` (2), `w615` (6) | 8 |
| `v2601_helicopter_urga_heavyassault_*` (3) | `main_weapon`, `secondary` | `w607` (2), `w606` (6) | 8 |
| `v4602_plane_urga_fighterbomber_*` (3) | `main_weapon`, `secondary` | `w611` (2), `w613` (6); `w612` (2) unbound | 8 |
| `v4800_plane_brothers_vintagefighter_*` (2) | `main_weapon` | `w617` (6) | 6 |
| `v2602_helicopter_urga_lightassault_*` (3) | `main_weapon` | `w604` (3) | 3 |
| `v4603_plane_urga_cargotransport_military_cargo_tank` | `main_weapon`, `secondary` (on the carried `CCar` root) | `w602` (1), `w603` (1) | 2 |

So "an aircraft with more than two guns on different points" exists only as **points inside two
components** — never as 3+ slots. The maximum points on a single bound weapon is **8**
(`w621` on 5 variants, `w609` on 3 variants).

## 6. Case E — several weapon points on one component

This is the normal shipped pattern, not the exception:

| weapon | points | note |
|---|---:|---|
| `w621_advancedhelicopter_missile` | 8 | rocket pod; 4 `fire_position_N` type 0 + 4 more (`wp13` §3) |
| `w609_fighterjet_missile_air_lockon` | 8 | `fire_point.0..7` |
| `w606_heavyhelicopter_missile` | 6 | 4 internal + 2 external `fire.point1/2` |
| `w617_vintagefighter_mgun` | 6 | all `internal.fire_point.N`, one slot |
| `w206_mounted_capstone_m2hm` | 4 | per boat slot (2 slots × 4) |
| `w622_advancedhelicopter_mgun` | 3 | `weapon.point.left/right` + 1 |
| `w601`, `w611`, `w615`, `w613` | 2–6 | per table §5 |

**One component firing from many points is fully shipped.** If the Batmobile needs more muzzles, the
files support adding points to a component; they do not support adding slots.

## 7. Case F — components that exist but are bound to nothing

| entity | component | points | bound |
|---|---|---:|---|
| `v4202_plane_capstone_fighterjet_*` (3 variants) | `w608_fighterjet_missile` | 2 | **no** |
| `v4602_plane_urga_fighterbomber_*` (3 variants) | `w612_fighterbomber_missile_air_lockon` | 2 | **no** |
| `v5603_train_urga_monorailmissilecar_military_01` | `w614_monorailmissilecar_missile` | — | **no** (entity has 0 bound slots) |

`WEAPON_WIRING.md` §2(b): "a component with no pointer is dead weight (the fighter jet ships one)".
This is the only shipped arrangement that resembles a *third* weapon: present, wired internally,
never referenced by a slot. Whether it can fire is UNKNOWN (no slot points at it).

## 8. Structural negatives (all measured on the 53 rows)

| test | result |
|---|---|
| roots with a duplicated slot **object id** | **0** |
| weapon objects bound to **more than one** slot (`binding` length > 1) | **0** |
| roots with a **non-null trailing pointer** (`id:8580BA42`, `id:CA86AA17`) | **0** |
| roots with **3 or more** non-null slot properties | **0** |
| roots mixing driver and gunner pointers | **0** |
| entities with **two roots that both carry weapons** | **0** (only compound entity, `v4603…cargo_tank`, has weapons on its `CCar` root only; the `CAirPlane` root's four pointers are null) |
| roots with two slots pointing at the **same target name** | **5** (Case A only) |

## 9. How the weapon UI would treat each case

The entity files carry **no selector state** (`WEAPON_WIRING.md` §2(b)): no active index, no
switch action, no group. `action_1`/`action_2` are `1`/`2` on armed and unarmed cars alike, so the
key-to-slot mapping is not in the data either. Therefore, per case:

| case | slots visible to the game | what can be said from files | what is UNKNOWN |
|---|---|---|---|
| A — two gunner slots, same weapon name | 2 distinct components, 2 mounts, 2 hinges | the two mounts aim independently (±75° each) and are separate weapons in physics | whether the selector shows **one** M2 entry or **two**, and whether one trigger fires both |
| B/C — driver pair, distinct names | 2 | two independent weapons (canon+MG; MG+rockets) | which key fires which (`WEAPON_WIRING.md` §2(b)) |
| D — 2 slots, up to 11 points | 2 | points are not selectable entries; they are muzzles | whether all points fire per trigger pull |
| F — unbound component | not visible | inert by the "dead weight" rule | whether it can fire at all |
| forced 8 slots | not shipped | nothing | whether the root reads a third pointer, and what the HUD lists |

## 10. Designs: shown vs not shown

Mapping each element of `wp13-slots-force.md` §6 to a shipped graph:

| # | design element | shipped? | evidence |
|---|---|---|---|
| 1 | one root, 2 driver slots non-null | **SHOWN** | 24 roots, `main_weapon` + `id:00568A74` |
| 2 | one root, 2 gunner slots non-null | **SHOWN** | 5 boat roots (§2) |
| 3 | two slots bound to two **distinct objects** of the **same weapon asset** | **SHOWN** | heavy patrol boat, 5 variants (§2) |
| 4 | two slots bound to **one shared weapon object** (same object id twice) | **NOT SHOWN** | 0 duplicate ids (§8) |
| 5 | **3 or more** non-null slots on one root | **NOT SHOWN** | max 2, 29 entities (§1) |
| 6 | **all four** pointers non-null on one root (`wp13`'s alternative) | **NOT SHOWN** | 0 |
| 7 | driver + gunner pointers non-null on the **same** root | **NOT SHOWN** | 24 driver pairs, 5 gunner pairs, 0 mixed |
| 8 | one entity with **two roots** | **SHOWN (structural)** | `v4603…cargo_tank.ee`: `CAirPlane` + `CCar` |
| 9 | an entity where **both roots carry weapons** | **NOT SHOWN** | plane root's four pointers null (§8) |
| 10 | 8 slots built as **four roots × 2 driver pointers** (`wp13` primary) | **NOT SHOWN** as a whole; elements 1 and 8 shown, the combination is not | §8 |
| 11 | a weapon with **many fire points** under one slot | **SHOWN** | `w621` 8 points, `w609` 8, `w617` 6 (§6) |
| 12 | a component present but **unbound** | **SHOWN** | `w608`, `w612`, `w614` (§7) |
| 13 | a slot property whose name is **not** one of the four | **NOT SHOWN** | 0; `wp13` §7.1 |

**What this does to the forced design.** The design's *load vocabulary* is proven: two slots can
each hold their own copy of one weapon asset and the game runs both as separate turrets (element 3).
What is *not* proven is any arrangement with more than two non-null slots, so the eight-slot plan
rests on **repeating the root** (element 8) rather than on a proven 8-slot root. `wp13`'s
alternative — one root with all four pointers non-null (element 6) — has **no** precedent at all and
is the weaker of the two by this evidence. The forced design should therefore:
1. keep **two slots per root** and get to eight by **four roots** (element 1 + 8), not by widening
   one root;
2. give every slot its **own weapon object** (element 3), never two pointers to one object
   (element 4 is unshipped);
3. keep driver pointers on some roots and gunner pointers on others only if the seat model is
   accepted — element 7 (mixed) is unshipped and element 9 (weapons on both roots) is unshipped,
   which is the design's largest single risk.

## 11. UNKNOWNs, each with the in-game check that would settle it

Written as pilot-card sentences (one observation, one variable, no code reading required).

| # | UNKNOWN | pilot-card sentence |
|---|---|---|
| U1 | does a root read a **third** non-null slot pointer? | "Spawn the eight-slot build, sit in the driver seat and press the weapon-cycle key: if the HUD lists more than two driver weapons, a root reads more than two slots; two means the extra pointers are ignored." |
| U2 | is a **shared object id** on two slots legal (element 4)? | "Spawn a test car whose two driver pointers name the same weapon object and press primary, then secondary: both keys firing one muzzle means one object can serve two slots; neither firing means the second pointer was rejected." |
| U3 | does the selector show **one or two** entries for two slots on one weapon asset? | "Board the heavy patrol boat, sit in the gunner seat and open the weapon selector: two identical M2 entries mean slots are listed independently; one entry means identical assets are merged." |
| U4 | does one trigger fire **both** boat cannons? | "Fire the heavy patrol boat's gunner control once while watching both mounts: both muzzles flashing means one trigger drives both slots; one means each slot has its own fire input." |
| U5 | do the two boat mounts aim **independently**? | "Aim the left mount at one target and the right at another: different bearings mean each slot owns its aim; the same bearing means one aim component serves both." |
| U6 | do **weapons on both roots** of one entity work? | "Enter the four-root Batmobile and look at the interaction prompt: a driver prompt plus a gunner prompt for each root means each root stands as its own seat; a single driver prompt means only one root is read." |
| U7 | does a **4-pointer single root** fire everything (`wp13` alternative)? | "Spawn the four-pointer build and press each fire key in turn: four different weapons firing means one root reads all four pointers; two means the last two are ignored." |
| U8 | does every fire point fire **per trigger pull**? | "Fire the advanced assault helicopter's rocket pod once and count the rockets: four leaving at once means every point fires per pull; one means the points are a sequential array." |
| U9 | can an **unbound** component fire (element 12)? | "Fly the fighter jet and press every weapon key: firing only the machine gun and the lock-on missile, never the internal two-point missile, confirms an unbound component cannot fire." |
| U10 | which key fires the **second driver** slot? | "Drive the Bavarium Tank and press primary and secondary in turn: a different weapon on each key means the two driver pointers map to the two fire inputs; both on one key means the mapping is elsewhere." |

## 12. Checks

| check | result |
|---|---|
| `WEAPON_WIRING.jsonl` rows read | 53 / 53 |
| bound histogram 0:1, 1:23, 2:29 | PASS |
| slot pairs restricted to the two patterns (24 + 5) | PASS |
| duplicate slot object ids | 0 (PASS) |
| weapons bound to >1 slot | 0 (PASS) |
| non-null trailing pointers | 0 (PASS) |
| repeated target names | 5 roots, all heavy patrol boat (PASS) |
| tank / Mstitel slot dumps reproduced | PASS (B: 2 slots / 2 points; C: 2 slots / 8 points) |
| boat mount parts and hinges cross-checked against `TURRET_LIMITS.md` | PASS (2 yaw + 2 pitch hinges, ±75°) |
| design table elements each backed by a measured count (§8) | PASS |
| game process started / attached / injected | none |

## 13. Sources

| source | location |
|---|---|
| 53 armed entities, slots, bindings, points | `Research/JC3Grab/WEAPON_WIRING.jsonl`; `WEAPON_WIRING.md` §1–§2 |
| heavy patrol mount hinges (±75°, `two_cannon`) | `Research/JC3Grab/TURRET_LIMITS.md` §1–§2 |
| forced 8-slot design under test | `tmp/freebuff/reports/wp13-slots-force.md` §5–§7 |
| compound cargo-plane entity (`CAirPlane` + `CCar`) | `v4603_plane_urga_cargotransport_military_cargo_tank.ee` row in `WEAPON_WIRING.jsonl`; `Research/JC3Grab/TETHER.md` §2 |
| "dead weight" unbound component rule | `Research/JC3Grab/WEAPON_WIRING.md` §2(b) |
| tank / Mstitel graphs | `WEAPON_WIRING.jsonl` rows for `v0202_car_capstone_bavariumtank_military_01.ee`, `v2601_helicopter_urga_heavyassault_military_01.ee` |
