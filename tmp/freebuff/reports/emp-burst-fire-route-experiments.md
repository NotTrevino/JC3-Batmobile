# EMP burst - which JC3 route fires it, the five experiments, and the build for the winner

Card: emp-burst-fire-route-experiments. 2026-11-07. Follows `tmp/freebuff/reports/T-WP5b.md` (decode
not restated here - every number below is quoted from it or from the file named beside it).

**Decision in one paragraph.** The burst is fired by **route (b), a `CEMPWeapon` in a driver weapon
slot**, with route (a)'s pulse copy as its payload. (b) is the only carrier in the fleet whose class
owns the disable *and* whose trigger already exists (the driver weapon button); (a) is the only
carrier whose entire EMP data difference can be copied byte for byte. The ranked order is
**(b) > (a) > (c) > (e) > (d)**, and the single blocking unknown is the same for all five: nothing in
either game's data says whether the victim stops. Each route therefore gets one pilot-card
experiment with a numeric pass band. **The winner's cost is a slot:** JC3 binds at most two driver
weapons, so the EMP takes the secondary slot that currently holds the Vulcan clone.

**Intended change / file / revert.** Creates one new file,
`tmp/freebuff/reports/emp-burst-fire-route-experiments.md`; correct because the brief names it and the
EMP lane's other artefacts sit in `Working/Translation/` (`T_WP5B_EMP_BURST.*`) and `tmp/freebuff/reports/`.
Nothing else is written. **Revert = delete this file.**

Labels as elsewhere: **decoded** = read in the cited file; **derived** = arithmetic/set logic on
decoded values; **UNKNOWN** = absent from every decoded file, with the probe that settles it.

---

## 1. Ranking - the five routes against four criteria

Criteria: **(F)** is there a fire button; **(D)** is the disable's owner decoded; **(C)** how much of
the burst's 16-member payload can the carrier hold; **(E)** evidence cost to settle.

| rank | route | closest JC3 system | F | D | C | E | verdict |
|---:|---|---|---|---|---|---|---|
| **1** | **(b) `CEMPWeapon` in a driver slot** | a **weapon** | yes - existing driver fire | **yes**: the class (`CEMPWeapon` token, exe `0x23E9428`; `.?AVCEMPWeapon@@` `0x2D6E058`) owns it, and the receiver is the vehicle-side state `is_disabled_by_emp` (exe `0x24EA080`) | range, cooldown, effect, sound slot, label | one entity edit + one shot | the only route where both the trigger and the disable's owner are already decoded; acceptance by a *vehicle* slot is the one gap |
| **2** | **(a) pulse copy, owned by a weapon component** | a **weapon-owned pulse** | yes - the missile/bullet fires it | no: the pulse carries the EMP's own flag triple, but no code owner is decoded | all of it except the impulses and the four levels | one entity edit + one shot | the shipped pattern already exists **25x** on `CMissileWeaponBase` and **29x** on `CBulletWeaponBase`, each on that weapon's own blast (`FORCEPULSE.md` §4.2); it is the closest *data* reproduction and needs no new class |
| **3** | **(c) the truck's use-item graph** | a **gadget action** | yes, but contextual (use-item) | no | prompt + trigger + effects | one entity merge + a save load | matches BmAK's own shape (`GA_BatmobileWeapon_EMPBurst`, `RInventoryGadget`) and the prompt `ui_activate_emp` is decoded, but the trigger has **no pointer** to the pulse and it needs a stunt-vehicle graph the car does not have |
| **4** | **(e) a `CCar`-owned pulse with the EMP flags, 0 damage** | a **vehicle pulse** | no - fires on the car's own event | no | the flag triple only | one entity edit + one shot | a **diagnostic**, not a firing route: it isolates whether the 3 flags alone disable, which decides if (a) can ride the car's own blast |
| **5** | **(d) a graph script fires it** | a **sequence event** | yes, once a node exists | no | only what the graph can set | decode graph bytecode | 1 non-owner reference in **307** pulses (`mm340` `GraphScript` -> `w704_m488`); the only route that could bind an arbitrary event, and the most expensive |

Why (b) beats (a) despite (a) being a bigger data copy: an EMP that fires on a missile's impact is a
different instrument - it is aimed, it lands where the missile lands, and it needs the victim to be
hit. BmAK's burst is centred on the car and needs no hit. Route (a) used **without** a weapon owner
(i.e. the car's own pulse) has no trigger at all, which is why (e) is the probe for it and not a
candidate.

## 2. The five experiment cards

All five need the test ban lifted (`tmp/freebuff/APPROVED_Q.txt`) and one new build tree,
`Builds/test-092`, layered over `Builds/test-091` the same way T-6 §4 layered test-091 over test-090.
Each card is one edit, one launch, one observation; PASS/FAIL is a number, not an impression.

### E1 - route (b): `CEMPWeapon` in the secondary driver slot

| step | exact action |
|---|---|
| 1 | In `Builds/test-092`, open the Batmobile entity (`v0300_car_kensington_sportsmuscle_batmobile`) and clone the `w503_turret_emp` entity into it (class `CEMPWeapon`; the turret variant carries a `CTurretWeaponComponent` and the 750 m / 500 dmg stock tune - the turret component and its `fire_position_1` `(0, 3.762, -9.708)` are the parts to strip, `EMP.md` §6) |
| 2 | Point the root's **secondary** slot (`id:00568A74`) at the clone's `_object_id` - that is the slot the Vulcan clone occupies today (T-HUD11), so it is a **swap**, not an addition (max driver weapons is 2, `WEAPON_WIRING.md`) |
| 3 | Copy `w503_turret_emp.wtunec` and set the range to **75 m** (`RBatmobileEMP.Range` 7500 uu = 75 m); leave damage as shipped for this run - the experiment is about the disable, not the number |
| 4 | Pack `test-092`, install, spawn the car, drive to a hostile APC at 40-50 m |
| 5 | Press the driver secondary fire once; watch the APC for 15 s |

**Pilot card:** *Fire the EMP at an APC at 40-50 m from the driver's secondary button - PASS = the
APC stops moving and stops firing within 1 s of the shot and stays stopped for at least 2 s, on 3/3
attempts, with no explosion; FAIL = the APC keeps driving, or dies (then the class accepts the slot
but the tune's damage kills before the state shows).*

Settles: whether a vehicle slot accepts `CEMPWeapon` (the one gap in route (b)) and, if it does, the
engine's actual disable duration - the number that replaces BmAK's 2/4/8/12 s ladder (§4).

### E2 - route (a): the EMP tune on a weapon-owned pulse

| step | exact action |
|---|---|
| 1 | In `Builds/test-092`, find the `w618_sportsmuscle_missile` component's `CForcePulse` - the pulse is the object the component owns through `id:B5AE7986` (`FORCEPULSE.md` §4.2) |
| 2 | Add a copy of the EMP pulse's members to it: `SettingsFile` -> a private copy of `truck_emp.ftune` with `PlayerDamageRadius`/`AIDamageRadius` = **25** and the rest as decoded (100/25/1/1); copy the flag triple as well - `id:4912FC04` 0, `id:AE6F7EFF` 1, `id:CF4F7880` 1. That triple is `0,1,1`, which **exactly one** of the fleet's 307 pulses carries, and it is this one (`EMP_DISABLE.json` `pulse.flag_triples`: `0,0,0` 16, `0,1,1` 1, `1,0,0` 278, `1,0,1` 12) |
| 3 | Leave the missile's own class and slot alone (`CMissileWeaponBase`, bound slot per T-11) - the pulse is the only edit |
| 4 | Pack, install, fire the missile at a stationary civilian car and at a hostile APC |

**Pilot card:** *Hit a civilian car with the edited missile - PASS = the EMP effect
(`explosion_emp_flatbed`) plays at the impact and the car stops for >= 2 s without being destroyed,
on 3/3; FAIL = normal blast only, or the car explodes.*

Settles: whether the pulse's flag triple - not the class - is what disables. If E2 passes, route (a)
can be the whole gadget with no new weapon class; if it fails, the flags are cosmetic and (b) is the
only route left.

### E3 - route (c): the truck's use-item graph on the car

| step | exact action |
|---|---|
| 1 | Merge the truck's three objects into the car entity: `trigger.use_item` (`CInteractionTrigger`, box at `(0, 1.3507, 2.396)`, 2x scale), `entry.use_item` (`CInteractionGraphEntry`, state `S_STUNT_USE_ITEM_VEHICLE`, prompt `ui_activate_emp`) and the `EMP` pulse with `truck_emp.ftune` (`EMP.md` §3/§7 copy list) |
| 2 | Add the `CPartProp` for the device (`oldtruck_emp_device_rebel`, index 5 on the donor) so the box sits on a real part, and give the car a stunt-vehicle interaction graph - the donor graph is what supplies `entry.use_item` (`EMP.md` §7) |
| 3 | Pack, install, stop the car inside the box's reach in a save, look for the prompt |

**Pilot card:** *Stop the car and press use-item - PASS = the `ui_activate_emp` prompt appears within
2 s on 5/5 stops and the pulse fires (EMP effect + the target stops); FAIL = no prompt (graph absent),
or the prompt appears and nothing fires (no link from state to pulse).*

Settles: the only decoded *gadget-shaped* trigger. Even on a pass it is contextual (the car must be
slow/stopped), so it cannot replace (b) as the on-demand burst - it can carry the charge/visual half.

### E4 - route (e): the flag triple alone, at 0 damage, on the car's own pulse

| step | exact action |
|---|---|
| 1 | Add a third `CForcePulse` to the car, owned by the car root through `id:B5AE7986` (the pattern 126 `CCar` pulses already use), tuned to `gen_explosion_5m_nodamage`-style numbers: `PlayerDamage`/`AIDamage` = **0**, radii 25, `*PercentageMax` 1 (`FORCEPULSE.md` §3 notes this tune as the 0-damage, push-only one that ships) |
| 2 | Copy the EMP's flag triple (`0,1,1`) and its material table reference `id:D3DDD766` -> `emp_flatbed_table` |
| 3 | Pack, install; detonate it (the vehicle's own blast path), with a cop car 5 m away |

**Pilot card:** *Detonate a 0-damage, EMP-flagged pulse 5 m from a police car - PASS = the cop stops
without taking damage, on 3/3; FAIL = it drives on (flags are cosmetic) or it takes damage (damage is
not separable from the pulse).*

Settles: whether a **vehicle-owned** pulse can carry the disable, which is the only way to get the
burst centred on the car without a weapon. This is the card that decides if route (a) can ever be
"the car's own blast".

### E5 - route (d): is there a graph node that fires a pulse

| step | exact action |
|---|---|
| 1 | Open `v4603_plane_urga_cargotransport_mm340.ee` and read the `CGraphScriptGameObject` named `GraphScript`; its `id:65424AC6` points at `875B9AD5=FFFF75FD`, that build's `BOMB_JEEP` `CVehicleRule` pulse (tune `w704_m488`) - the fleet's **only** non-owner pulse reference |
| 2 | Decode the graph's node list with the existing `.gdc`/`.gsc` reader and look for a node type whose argument is that object id |
| 3 | No game launch needed for step 2; only if a node exists does this route get a build |

**Pilot card:** *Decode the mm340 `GraphScript` node list - PASS = one node names the pulse object id
(route (d) is live and can bind an arbitrary event, e.g. the EMP key); FAIL = no node names it (the
reference is a stale pointer and route (d) closes).*

Settles: the only route that could fire the burst from a *sequence event* rather than a weapon. It is
ranked last because a file-only check can sit behind two in-game experiments.

## 3. Build composition for the winner - route (b) + (a)'s payload

Fifteen members have a carrier; one has none. Numbers are the 16 decoded members
(`Working/Translation/T_WP5B_EMP_BURST.md` §1/§2), not re-derived here.

### 3.1 Objects to author

| # | object | from | why |
|---:|---|---|---|
| 1 | weapon component, class `CEMPWeapon` | `w503_turret_emp`, turret component and fire point stripped | the class that owns the disable |
| 2 | root slot binding | the car's **secondary** slot (`id:00568A74`) | the only free slot; **swaps out the Vulcan clone** (2-slot cap, `WEAPON_WIRING.md`) |
| 3 | private weapon tune | copy of `w503_turret_emp.wtunec`, `range` 75 m | BmAK `Range` 75 m; stock is 750 m |
| 4 | `CForcePulse` named `EMP`, owned by the component via `id:B5AE7986` | `truck_emp.ftune` copy | the shipped weapon-owned-pulse pattern (25 missile / 29 bullet instances) |
| 5 | pulse tune copy | `truck_emp.ftune`: damage 0, radius 75, `PercentageMax`/`Min` 1 | 75 m from `Range`; damage 0 because the burst has no damage member, only impulses; full-radius hold is the EMP's own shape |
| 6 | material effect table | `emp_flatbed_table` (`id:D3DDD766`) | the only EMP-named visual binding |
| 7 | discharge effect | `explosion_emp_flatbed.effc` | the one EMP effect file that ships |
| 8 | charge effect | `emp_active.effc` / the mm250 `epe_emp_powering_up` emitter | no BmAK particle can be taken; this is the fleet's charging prop |
| 9 | label | "EMP Burst" (`TempName`) | the display name |

### 3.2 Member-by-member

| member (16) | value | carried by | gap |
|---|---|---|---|
| `Range` | 75 m | tune `range` 75 (#3) | none |
| `DisableEnemyDuration[4]` | 2/4/8/12 s | **nothing in data** - code-side `CEMPWeapon`; bind level 1 | the ladder is UNKNOWN until E1 measures the engine's actual stop (§4) |
| `ChargeParticle` | `EMP_Burst_Charge` | #8 | BmAK particle absent; JC3 stand-in only |
| `PowerLevelChargeTime[4]` | 0/0.5/1/1.5 s | tap only (0 s) | hold-to-charge has no JC3 input; the four levels collapse to one |
| `FireParticle[4]` | `Stage_01..04` | #7, one effect | 4 stages -> 1 |
| `EMPFireSound` / `EMPFireSwitch` | `Play_Batmobile_EMP`, 4 switches | existing weapon fire event | BmAK banks absent (T-AU3) |
| `EMPFFWaveForm` | - | none | no force-feedback member decoded |
| `ImpulseComponent` | 15000, `RIF_Constant`, `RDmgType_Explosion` | the 0-damage pulse's push (#5) | no impulse number in any JC3 pulse tune (8 numbers, none an impulse) |
| `ChargeStartTime` | - | tap | none |
| `ChargingEMP` / `bButtonPressed` | bools | code state | no member |
| `EMPImpulse` / `EMPVehicleImpulse` | 5000 / 20000 | none | no per-target impulse member |
| `PowerLevel` / `MaxPowerLevel` | 4 levels | 1 | derived: one pulse, no levels |
| cooldown (archetype) | 2 s | tune fire interval 2 s | none |
| `PowerConsumption` | 1 | none | JC3 has no vehicle power pool |
| `TempName` | "EMP Burst" | label (#9) | none |
| `GadgetType` | `GA_BatmobileWeapon_EMPBurst` | slot identity | no JC3 gadget type |
| `MaterialToUpdateWhenPresent` | wheel EMP material, slot 0 | part material override, **if** the swap test passes | no decoded member swaps a material on a state; T-WP5b §7 leaves wheels UNKNOWN |
| trigger | tap `[3]` / `{PAD_B}`, hold as level 2 | driver secondary button | hold detent dropped with the levels |

## 4. The disable-duration question

**Answer: JC3 disables a vehicle through a code-side vehicle state, and no decoded file gives that
state a duration - so 2/4/8/12 s cannot be authored in data; the build binds the 2 s level and
measures what the engine actually does.**

| what | value | evidence |
|---|---|---|
| the disable's owner | `CEMPWeapon` class | exe tokens `.?AVCEMPWeapon@@` 0x2D6E058, `CEMPWeapon` x6 0x23E9428 (`EMP_DISABLE.json` `exe.tokens`) |
| the receiver state | **`is_disabled_by_emp`** - a vehicle-side script variable name, in the vehicle variable-name block at 0x24EA080 | `EMP_DISABLE.json` `exe.variable_name_block`; **0** hash occurrences of `is_disabled_by_emp` in the whole `.ee` corpus (`data.hash_occurrences`) - it is a state, not a data member |
| that the state is timed by code | `enemy.mech.exit_emp_state` string, exe 0x24D5238 | same file - an exit transition exists, and no duration member feeds it |
| vulnerability gate | `SetVehiclePartVulnerability` (exe 0x241B020) + `electricity_armor` (hash 0x0B4ACB5C, **1** entity: `v0403_car_mugello_modernecosuper_civilian_01`) | same file - EMP immunity is per part, not a duration |
| does any JC3 tune hold a duration? | no - 23 `ForcePulseSettings` tunes, 8 numbers each, none named duration or target class; neither `CEMPWeapon` tune has an EMP field | `FORCEPULSE.md` §1/§3, `EMP.md` §6 |
| **closest authorable timer in data** | `*_engine_shut_down_delay_s` = **30 s** (car) / **5 s** (boat, bike, helicopter, plane), in the shared `vehicle_common` module | `WATER.md` lines 229-233 - a real per-vehicle engine-shutdown timer, keyed to **water entry**, not EMP, and shared fleet-wide (a private copy would be needed, R7) |

**What that means for the build.** The duration is not a knob, it is a code outcome. Bind level 1
(the 2 s rung), and let E1 read the real number back: if the victim stops for ~2 s the ladder's first
rung is reproduced; if it stops for another fixed time, or not at all, the row is recorded as
UNKNOWN with the measured seconds and the ladder is not shipped. The `engine_shut_down_delay_s` field
is named as the *closest* duration carrier and explicitly **not** used: re-keying a water timer to EMP
has no evidence, and taking a private `vehicle_common` copy would move a fleet-wide module for one
gadget.

## 5. What this changes in the plan

1. The burst's firing route is **(b)**, not the pulse copy the compromise recommended - because a
   pulse with no owner has no button, and (a) only has one when a weapon owns it.
2. The **secondary slot** is the price: the Vulcan clone loses its slot (2-slot cap). Alternative if
   that is unacceptable: ship the burst on route (c) as a contextual use-item action and accept that
   it cannot be fired while driving fast.
3. The **impulse and the four power levels are gone** in every route; E1/E2 cannot bring them back.
4. The disable's **duration** is measured, not authored (§4); no row may claim 2/4/8/12 s after the
   build without E1's number.

## 6. Checks run for this card

| check | result |
|---|---|
| five routes from `T-WP5b.md` | each has a ranked row, a card, and a named pass band; none closed as "JC3 cannot" |
| flag triple counts | `0,0,0` 16 / `0,1,1` 1 / `1,0,0` 278 / `1,0,1` 12, `pulses` 307 - re-read in `Research/JC3Grab/EMP_DISABLE.json` |
| `is_disabled_by_emp` | 0 hash occurrences in `data.hash_occurrences`, 1 exe token at 0x24EA080, name present in `exe.variable_name_block` at 0x24ea080 |
| `CEMPWeapon` | 2 exe tokens (mangled + plain), 0 of 88 vehicle weapon components (`EMP.md` §6) |
| engine shutdown delays | `car_common` 30, boat/helicopter/motorbike/plane 5 s, 232 vehicles, `WATER.md` 229-233 |
| dispatch slots | 2 driver weapons max (`README.md` §Weapon wiring), so the EMP swap is a real constraint, not a preference |
| game launched / packed / installed | **no** - the experiments are specified, not run (test ban); nothing written outside this file |
