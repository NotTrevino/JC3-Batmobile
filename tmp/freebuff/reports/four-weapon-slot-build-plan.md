# Four independently selectable Batmobile weapons - build plan

Card: four-weapon-slot-build-plan. 2026-11-07. Reads `tmp/freebuff/reports/T-WP13b.md`,
`Working/Translation/T_WP13B.md`, `Research/JC3Grab/WEAPON_WIRING.md`, `JC3_HUD_WEAPONS.md`,
`INPUT.json` (via T-WP13b §4b) and `lock-on-reticle-hud-link.md`. No decode is restated beyond the
numbers a build step needs.

**Plan in one paragraph.** JC3 already gives the car **four slot properties** - `main_weapon`
(`id:851CAABE`, driver), second driver (`id:00568A74`), `mounted_weapon` (gunner), `mounted_weapon_2`
(`id:AC0BC788`, gunner) - all four on 54/54 roots, plus **two never-used pointers**
(`id:8580BA42`, `id:CA86AA17`, non-null on **0** of 54). The entity is therefore not the limit; the
limit is **two fire paths** (`FIRE_VEHICLE_WEAPON_PRIMARY` RSHOULDER/MOUSE1,
`FIRE_VEHICLE_WEAPON_SECONDARY` LSHOULDER/MOUSE2, both land-vehicle, and **no** land-vehicle weapon
selector). The build puts the cannon and the Vulcan on the two proven slots, the missile launcher on
spare pointer `id:8580BA42` (a **second weapon component**, fired from `USE_VEHICLE_MOD` = d-pad
right), and the EMP on a **gadget** - the truck's use-item graph - because that is the only fourth
action whose trigger and prompt are already decoded. The two gunner pointers stay empty deliberately:
they are a proven fire path in the wrong seat.

**Intended change / file / revert.** Creates one new file,
`tmp/freebuff/reports/four-weapon-slot-build-plan.md`; correct because the brief names it and the
slot lane's other artefacts are `Working/Translation/T_WP13B.md` and `tmp/freebuff/reports/T-WP13b.md`.
Nothing else is written. **Revert = delete this file.**

**Reconciliation with the EMP card.** `tmp/freebuff/reports/emp-burst-fire-route-experiments.md` puts
the EMP in the **secondary** slot, because that is what its experiment E1 tests. This plan supersedes
that *binding*, not that test: if four slots ship, the Vulcan keeps the secondary slot (BmAK's own
menu binds the Vulcan to RB) and the EMP moves to the gadget path. E1 is still the way to prove the
disable; the four-slot plan then re-homes the proven object.

Evidence levels used per step: **decoded** (file + field), **derived** (set logic on decoded values),
**authored** (a build choice no file makes), **UNKNOWN** (with the file or probe that settles it).

---

## 1. What the entity already has (decoded)

| item | value | source |
|---|---|---|
| slot properties per root | **4**, on 54/54 roots | `T_WP13B.md` §1, O2 |
| bound | `main_weapon` 38, `secondary (id:00568A74)` 24, `mounted_weapon` 14, `mounted_weapon_2` 5 | same |
| driver-fired | **2** (`main_weapon`, `secondary`); gunner holds the other two, gated by `S_IDLE_VEHICLE_SPINNING_MOUNTED_WEAPON` | same, O3 |
| max driver slots on any graph | **2** (histogram 0:15, 1:14, 2:24) | same, O4 |
| spare pointers | `id:8580BA42`, `id:CA86AA17` - same class/shape as a slot, **non-null on 0** of 54 | `WEAPON_WIRING.md` §1; T-WP13b O5 |
| max weapon components on one entity | **3**; 7 graphs carry a component no slot points at | `WEAPON_WIRING.md` §2c |
| fire paths | 2 land-vehicle actions; the only selector actions (`NEXT_WEAPON`, `PREV_WEAPON`) are keyboard-only and **on-foot** | T-WP13b §4b, O10 |
| BmAK model | **4 indices, one button each** (1 B, 2 X, 3 Y, 4 d-pad up); an index is a *fire* path, not a stored selection | T-WP13b §4a, O7/O8/O9 |
| HUD slots | **2** clips (`MCI_vehicle_weapons0/1`) | `JC3_HUD_WEAPONS.md` §3; T-WP13b O11 |

So "four weapons" costs exactly one thing the files do not have: **two more fire paths**. Everything
else - pointers, components, art, icons - already ships.

## 2. The plan at a glance

| slot | BmAK index / button | weapon | JC3 slot property | fire path | mechanism class | evidence |
|---:|---|---|---|---|---|---|
| 1 | 1 · B (battle) | WPN-1 Heavy Cannon (60mm) | `main_weapon` (`id:851CAABE`) | RSHOULDER / MOUSE1 | existing slot | **decoded**: the medium tank binds `w602_mediumtank_canon` to this property (`WEAPON_WIRING.md` §4) |
| 2 | 2 · X (battle) | WPN-2 Vulcan chain gun | secondary (`id:00568A74`) | LSHOULDER / MOUSE2 | existing slot | **decoded**: `w603_mediumtank_mgun` on the same property, the only land chassis with both driver slots bound |
| 3 | 3 · Y (battle) | WPN-3 Missile launcher | spare `id:8580BA42` | `USE_VEHICLE_MOD` (d-pad right / MOUSE3), **displacing turbo jump** | **a second weapon component** | pointer **decoded** (present, null); its firing **UNKNOWN** - probe P1 |
| 4 | 4 · d-pad up (battle) | WPN-4 EMP missile / WPN-5 burst | no slot: a gadget | use-item (`S_STUNT_USE_ITEM_VEHICLE` + prompt) | **a gadget** | objects **decoded** (`EMP.md` §3), link from state to weapon **UNKNOWN** - probe P4 |

Why the cannon/Vulcan are on 1/2 and not on 3/4: the two proven slots are the only two the engine is
*known* to fire from the driver seat, and BmAK's own menu puts the cannon and the Vulcan on the two
triggers (RT/RB) - so the pair that must never fail sits on the pair that already works.

## 3. The four slot properties, and what each is for in this build

| property | seat that owns it | bound in fleet | this plan |
|---|---|---:|---|
| `main_weapon` (`id:851CAABE`) | driver | 38 | slot 1, cannon |
| secondary (`id:00568A74`) | driver | 24 | slot 2, Vulcan |
| `mounted_weapon` | gunner | 14 | **not used** - proven path, wrong seat (probe P2 asks whether the driver can borrow it) |
| `mounted_weapon_2` (`id:AC0BC788`) | gunner | 5 | **not used**, same reason |

**Derived:** 14 + 5 bound gunner slots prove the engine fires a weapon behind *those* pointers (with
a pawn seated), which is stronger evidence than the spares have (0 non-null anywhere). The reason they
are not the plan's slots 3/4 is scope, not doubt: they fire for a *gunner*.

## 4. The two spare pointers - what they are used for

| pointer | enough evidence to write? | what the build puts there | what is still unknown |
|---|---|---|---|
| `id:8580BA42` | yes: same root class, same object-reference shape as a weapon slot, present on all 54 roots | **slot 3**: the missile-launcher component (a second `CBulletWeaponBase`/`CMissileWeaponBase` next to the cannon) | whether the engine **reads** the pointer at all, and if it does, **which action** fires it |
| `id:CA86AA17` | same | **spare** - reserved for the EMP if the gadget route fails (P4), otherwise left null | same |

**The probe that settles both, before any build work (P1, 5 minutes):** on
`v0201_car_capstone_mediumtank_debug.ee`, point `id:8580BA42` at a copy of `w602_mediumtank_canon`
(keeping the real `main_weapon` bound to the original), pack, install, and press **every** driver
button once in order: RSHOULDER, LSHOULDER, d-pad right, d-pad down.

**Pilot card (P1):** *Medium tank, spare pointer #1 loaded with a copied cannon - PASS = one extra
cannon round leaves the muzzle on exactly one of the four buttons, on 3/3 presses of that button and
0/13 presses of the other three; FAIL = no round on any button (the pointer is decorative).*

If P1 passes it also names the button the spare rides, which decides whether slot 3 needs the d-pad
rebind at all. If it fails, slot 3 falls back to **mode sharing** (§5.3).

## 5. Third and fourth fire paths - mechanism ranking

### 5.1 The three candidate mechanisms, ranked for *this* car

| rank | mechanism | what the files prove | what it costs | verdict |
|---:|---|---|---|---|
| **1** | **a second weapon component behind a spare pointer** | components without slots already ship (max 3 components/entity, 7 graphs with an unbound one); the spare is the only decoded driver-scope write target | one pointer write + one component + its tune | **slot 3** - cheapest, and the probe is 5 minutes |
| **2** | **a gadget (use-item graph)** | trigger box, entry state `S_STUNT_USE_ITEM_VEHICLE`, prompt `ui_activate_emp`, pulse object - all decoded on one truck | needs a stunt-vehicle interaction graph on the car; fires only when stopped/slow | **slot 4** - the only fourth action that needs no new pointer and no new button |
| **3** | **a sequence event (graph script)** | exactly **1** non-owner pulse reference in 307 pulses (`mm340` `GraphScript` -> `w704_m488`) | graph bytecode undecoded; no decoded binding from a graph to a vehicle input action | **fallback only** - right mechanism for a mission, not for a button |

### 5.2 Why not "just add a third slot"

The entity would accept it (four properties, three components/entity is normal). What is missing is
an **action** to pull the trigger: `TryToFireWeapon` has **0 rows** in `INDEX.jsonl`, so JC3's
per-weapon fire is native and there is no script to clone from two actions to four. That is why the
plan buys paths one at a time (pointer -> gadget -> graph) instead of adding slots and hoping.

### 5.3 Fallbacks, in order

1. **P1 passes** -> slot 3 on the spare, button as observed.
2. **P1 fails, P2 passes** (driver may fire a gunner slot) -> slot 3 on `mounted_weapon`, slot 4 on
   `mounted_weapon_2`; no gadget needed, both pointers already prove the engine fires them.
3. **P1 and P2 fail** -> **mode sharing**, which is BmAK's own behaviour: one physical button carries
   the battle weapon and the pursuit weapon (`EMP` on B in battle, `Tracker` on B in pursuit,
   `T_WP13B.md` §4a). Four weapons stay reachable as two buttons x two modes; the status is
   **derived**, not decoded.
4. **Slot 4 always** has the gadget path, so the fourth weapon does not depend on 1-3.

## 6. Button mapping

| slot | BmAK button (index) | JC3 action | input | displaced JC3 action | evidence |
|---:|---|---|---|---|---|
| 1 | `XboxTypeS_B` (1) | `FIRE_VEHICLE_WEAPON_PRIMARY` | RSHOULDER / MOUSE1 | none | decoded (`INPUT.json` via T-WP13b §4b) |
| 2 | `XboxTypeS_X` (2) | `FIRE_VEHICLE_WEAPON_SECONDARY` | LSHOULDER / MOUSE2 | none | decoded |
| 3 | `XboxTypeS_Y` (3) | `USE_VEHICLE_MOD` | RPADRIGHT / MOUSE3 | **turbo jump** (`turbo_jump` block on 145 vehicles) | action decoded; the displacement is **authored** under the operator's 2026-11-05 rule (BmAK buttons win inside the car) |
| 4 | `XboxTypeS_DPad_Up` (4) | use-item (`PUSH_GRAPPLE` / `USE` family, on-foot style prompt) | contextual | nothing - the prompt only appears when eligible | prompt/state **decoded** (`EMP.md` §3); the input that raises it in a car **UNKNOWN** |

Two honest notes. **(a)** BmAK's index-to-weapon map is **UNKNOWN** (`DRIVINGMODE.md` §4: literals
decoded, object not), so "index 1 = cannon" is an authored assignment; what is decoded is that each
index has its own button and that pressing it fires. **(b)** MOUSE2 is bound to *both*
`FIRE_VEHICLE_WEAPON_SECONDARY` and `FIRE_GRAPPLE` (the latter unscoped), so on keyboard slot 2 and
the grapple share a key - a shipped ambiguity, not one this plan creates.

`VEHICLE_RELEASE_GRAPPLE` (d-pad down / V) is deliberately **not** used: it is the only vehicle-scope
tether action in the game and `T_WP13B.md` §7 needs it for the winch.

## 7. HUD selection feedback

JC3 shows **two** slot clips (`MCI_vehicle_weapons0/1`) and the icon is a file named by weapon id
(`textures/ui/weapon_icons/<id>.ddsc`; ids -1 and 0 rejected). There is **no armed-weapon indicator**,
because there is no selection state - and BmAK has none either (`SelectVehicleWeapon` is a fire body).
So the feedback model is "**the weapon that just fired lights its slot**", not "a selector moves".

| need | JC3 member | evidence | build step |
|---|---|---|---|
| slot 1/2 identity | `InitVehicleWeapons(slot 0/1, weapon_id, name, …)` | decoded, `JC3_HUD_WEAPONS.md` §1 | call once at spawn with 602 / 603 clones |
| slot 1/2 ammo + cooldown | `UpdateVehicleWeapons(slot, mag, total, low, cooldown, overcharged)` | decoded §2 | call per shot |
| icon per weapon | `weapon_icons/<id>.ddsc`; `LoadIcon` skips -1/0 | decoded §6 | pick ids that have icons (602, 603 ship; **614 does not**) |
| feedback for the weapon just fired on slots 3/4 | re-call `InitVehicleWeapons` on one of the two clips with that weapon's id, then `InitVehicleWeapons` back | **derived**: only `Init` sets the id (`Update` cannot change it, §2) | authored flash: show the fired weapon's icon on clip 1 for 1.5 s |
| a permanent third/fourth clip | **none** - `m_WeaponsArray` is hard-sized to 2 (`VehicleConstructor`) | decoded §3 | authored private `ui/hud.gfx` extension with `MCI_vehicle_weapons2/3`, driven by the same graph that fires them |
| reticle per weapon | `UpdateWeaponReticle(show, look, size, shape)` - 14 shapes, `E_RETICLE_CANNON` 8 exists but its vehicle binding is native | decoded §4, T-HUD14 | author shape per weapon as a build choice; record as UNKNOWN binding |

**Decision:** ship §7 rows 1-4 (stock HUD, two clips, fired-weapon flash) and defer the private
movie (`weapons2/3`) to a separate BUILD card - it is the only way to show four slots at once and it
needs art, not data.

## 8. Shipped entities that already carry unreferenced weapons

These are the precedent that a component can exist without a slot - and the proof that "carried" is
not "fired".

| entity | components | bound | carried, unbound | source |
|---|---:|---:|---|---|
| `v4202_plane_capstone_fighterjet_debug.ee` | 3 | 2 | `w608_fighterjet_missile` | `WEAPON_WIRING.md` §2c |
| `v4202_plane_capstone_fighterjet_military_01.ee` | 3 | 2 | `w608_fighterjet_missile` | same |
| `v4202_plane_capstone_fighterjet_rebel_01.ee` | 3 | 2 | `w608_fighterjet_missile` | same |
| `v4602_plane_urga_fighterbomber_debug.ee` | 3 | 2 | `w612_fighterbomber_missile_air_lockon` | same |
| `v4602_plane_urga_fighterbomber_military_01.ee` | 3 | 2 | `w612_fighterbomber_missile_air_lockon` | same |
| `v4602_plane_urga_fighterbomber_rebel_01.ee` | 3 | 2 | `w612_fighterbomber_missile_air_lockon` | same |
| `v5603_train_urga_monorailmissilecar_military_01.ee` | 1 | **0** | `w614_monorailmissilecar_missile` | same |

Plus the build's own car: the current `.epe` carries **4** `CBulletWeaponBase` components and **2**
unbound weapons (`lock-on-reticle-hud-link.md` §4, `counts.unbound_weapons = 2`) - i.e. the
Batmobile already has the "extra component, no pointer" state the plan is built on.

## 9. Build steps

| # | step | file / object | evidence | revert |
|---:|---|---|---|---|
| B1 | keep `w602` cannon clone on `main_weapon`, `w603` Vulcan clone on `secondary` | root `CCar` slots of the built `.ee` | decoded (medium-tank precedent) | restore the two pointers |
| B2 | write `id:8580BA42` -> a new missile component (`CMissileWeaponBase`, private tune) | root object of the built `.ee` | pointer decoded; firing UNKNOWN (P1) | null the pointer |
| B3 | bind the missile's fire to `USE_VEHICLE_MOD` (d-pad right), accepting the turbo-jump loss | input/config layer | action decoded, displacement authored | restore the turbo-jump binding |
| B4 | add the truck's EMP as a **gadget**: `trigger.use_item` box + `entry.use_item` -> `S_STUNT_USE_ITEM_VEHICLE`, prompt `ui_activate_emp`, `EMP` pulse | built `.ee` + its interaction graph | objects decoded (`EMP.md` §3), state->pulse link UNKNOWN (P4) | remove the three objects |
| B5 | give the car a stunt-vehicle interaction graph (the truck's is the source) | entity graph | decoded that the donor graph supplies `entry.use_item` (`EMP.md` §7) | drop the graph |
| B6 | HUD: `InitVehicleWeapons(0/1, …)` for cannon/Vulcan, `UpdateVehicleWeapons` per shot, fired-weapon icon flash on clip 1 | graph/HUD caller | decoded API; flash is authored | stop calling |
| B7 | per-weapon reticles via `UpdateWeaponReticle(shape)` | same caller | shape ids decoded, vehicle binding UNKNOWN | leave shape 8 for all |
| B8 | four visible slot clips (`MCI_vehicle_weapons2/3`) | **private `ui/hud.gfx`** | authored - no stock member | rebuild stock hud.gfx |

## 10. Pilot cards - one per weapon slot

**Slot 1 - cannon.** *Empty lot, target 50 m ahead: press RSHOULDER once - PASS = exactly one cannon
round leaves the muzzle within 0.2 s and the target takes cannon-class damage, on **10/10** presses,
with **0** rounds from the Vulcan, the missile and the EMP in the same window.*

**Slot 2 - Vulcan.** *Same target: hold LSHOULDER for 1 s - PASS = >= 10 rounds in that second, the
cannon silent, and the ammo/cooldown clip for slot 1 unchanged, on **5/5** holds.*

**Slot 3 - missile.** *Press d-pad right with no target - PASS = one missile launches (not a turbo
jump and not a cannon round) on **8/8** presses, the car does not jump, and the slot-1 clip shows the
missile icon within 1.5 s of the launch; FAIL = a jump, or no launch after P1 passed.*

**Slot 4 - EMP gadget.** *Stop the car beside a hostile APC: PASS = the `ui_activate_emp` prompt
appears within 2 s and firing it produces the EMP effect on **5/5** stops; and above 20 km/h the
prompt does **not** appear on 5/5 passes (this documents the contextual limit rather than failing
it).*

## 11. UNKNOWNs - and the file or probe that settles each

| # | unknown | settles it |
|---|---|---|
| 1 | whether `id:8580BA42` / `id:CA86AA17` fire a weapon at all | probe **P1** (medium tank, spare loaded with a copied cannon); the reader is native and in no decoded package |
| 2 | which button a firing spare rides | same probe - the observed button is the answer |
| 3 | whether a driver can fire a gunner slot with nobody seated | probe **P2** (APC, `mounted_weapon` bound, driver only) |
| 4 | whether a graph can bind to a vehicle input action (sequence-event path) | decode the `mm340` `GraphScript` node list (`v4603_plane_urga_cargotransport_mm340.ee`, `id:65424AC6` -> `875B9AD5=FFFF75FD`) |
| 5 | the link from `S_STUNT_USE_ITEM_VEHICLE` to the pulse | probe **P4** (car + truck graph, press use-item) |
| 6 | the index -> weapon map inside BmAK | `DRIVINGMODE.md` §4 (literals decoded, object not) |
| 7 | whether a vehicle cannon's reticle shape is `E_RETICLE_CANNON` (8) | TEST observation; `JC3_HUD_WEAPONS.md` §4 has the ids, no binding |
| 8 | whether `InitVehicleWeapons(2, …)` is safe with a third clip added | the private-movie build (B8) + `hud.as` `VehicleConstructor`'s two-element array |

## 12. Checks run for this card

| check | result |
|---|---|
| four slot properties, per-seat split | re-read from `T_WP13B.md` §1 (54/54 roots; 2 driver, 2 gunner) |
| spare pointers | `id:8580BA42`, `id:CA86AA17`, seen 54, non-null 0 (`WEAPON_WIRING.md` §1) |
| fire paths | 2 land-vehicle actions; 0 land-vehicle selectors (`T-WP13b` O10) |
| BmAK indices/buttons | 4 indices, one button each (O7/O8), index is a fire body (O9) |
| unbound-weapon entities | 7 graphs / 3 chassis re-read from `WEAPON_WIRING.md` §2c |
| HUD capacity | 2 clips, array hard-sized 2 (`JC3_HUD_WEAPONS.md` §3) |
| slot count vs evidence | 4 slots planned; 2 have decoded carriers, 1 is a candidate pointer, 1 is a gadget - stated per row, none presented as decoded |
| game launched / packed | **no** - probes P1/P2/P4 are specified, not run (test ban); nothing written outside this file |
