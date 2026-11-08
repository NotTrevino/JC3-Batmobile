# T-MD2 / T-WP4 / T-WP5 — the Immobiliser: where JC3 disables a vehicle, and the missing link

**Card:** T-MD2 (Immobilizer, EMP missile) and T-WP5 (EMP burst). Both rows say the same thing: a
`w618` missile clone and an entity-level `CForcePulse` copy can be built, but **nothing observed
stalls the target**. This report searches JC3 for the disable itself — engine kill on damage, the
EMP/Bavarium vocabulary, the stalled-engine state in `vehicle_common`, the electric/shock damage
channel, and any state setter reachable from a weapon or a force pulse — and either gives the
member chain from effect to stalled vehicle, or names the missing link.

**Verdict in one paragraph.** The **effect** half exists and is decodable: the pulse object, its
`truck_emp.ftune` (100 damage in 25 m at full radius), its three unique flag values and its
position are all in the files, and the missile half is a `w618` clone. The **state** half exists
**only in the engine**: `JustCause3.exe` carries a per-vehicle variable named `is_disabled_by_emp`
in its vehicle-variable vocabulary (0x24EA080, next to `engine_damage`, `engine_torque_max`,
`is_frozen`), and an EMP weapon class `CEMPWeapon` that ships as `w702_emp` (handheld) and
`w503_turret_emp` (static turret). **No shipped asset binds either one to anything**: the literal
name occurs **0** times in 1,941 decoded entries (3.98 GB) and its Jenkins hash `0x0A6B5E46` occurs
**0** times in 1,307 entity entries (3.96 GB), while the controls `invulnerable` (289) and
`is_in_water` (160) hit on the same pass. So the missing link is not a value: it is **the writer**
of the disable state. JC3's damage/engine/stall members can damage, slow or drown a vehicle, but
none of them can turn its engine off. The **closest system** is the engine's own `CEMPWeapon`
class; the **gap the build fills** is mounting that class in a vehicle weapon slot (data cannot
decide whether the engine accepts it) and, if the pulse route is preferred, finding what fires an
unowned pulse. Both are one-probe questions, not missing numbers.

## 1. BmAK side — what "Immobilizer" is, and which of its numbers actually ship

`RBatmobileEMP` `Batmobile_EMP_Burst` exists in **3** packages (`Playable_Batmobile_SF`,
`_MK2_SF`, `_Funhouse_SF`), 2,552 B, super `RVehicleWeapon`; `RBatmobileEMPMissile`
`Batmobile_EMP_Missile_Launcher` is the launcher (63 fields) and `RBatmobileMissile`
`Batmobile_EMPMissile_Projectile` / `…_ForCars` are its projectiles
(`Research/BatmobileGrab/BMSDK_OFFSETS.json`, `ASSETS.md`).

| member | offset | kind | shipped value |
|---|---:|---|---|
| `Range` | 2396 | float | **not serialised** on the instance (UNKNOWN — class default) |
| `DisableEnemyDuration` | 2400 | array\<float\> | **not serialised** (UNKNOWN — the disable's duration) |
| `PowerLevelChargeTime` | 2424 | array\<float\> | not serialised |
| `ChargeStartTime` | 2504 | float | not serialised |
| `ChargingEMP` / `bButtonPressed` | 2508 | bool bit 1 / bit 2 | runtime flags |
| `EMPImpulse` | 2512 | array\<float\> | not serialised |
| `EMPVehicleImpulse` | 2528 | array\<float\> | not serialised |
| `PowerLevel` / `MaxPowerLevel` | 2544 / 2548 | int | not serialised |
| `ChargeParticle` | 2416 | ParticleSystemComponent | `Batmobile_EMP_Burst.ChargeParticle0` (5085) |
| `FireParticle` | 2440 | array | tag serialised, count 4 |
| `EMPFireSwitch` | 2472 | array\<AkSwitchName\> | tag serialised, count 4 |
| `ImpulseComponent` | 2496 | `RB_RadialImpulseComponent` | `Batmobile_EMP_Burst.ImpulseComponent0` (5195) |
| `EMPFireSound` | 2456 | array\<AkEvent\> | `Engine.Play_Batmobile_EMP` ×2 |
| `EMPFireSwitch`/materials | 2232/2240 | MaterialInstanceConstant | `Batmobile_V3_Wheel_EMP_MAT_INST`, `Batmobile_V3_Wheel_V2_MAT` |

Serialised tags on all three bursts are exactly offsets
`{360, 792, 2096, 2176, 2200, 2232, 2240, 2348, 2416, 2440, 2472, 2496}`
(`Research/JC3Grab/EMP_DISABLE.json` → `bmak.serialized`, from `objects.jsonl`). **The disable is a
named float array, `DisableEnemyDuration`, and even BmAK does not serialise its value** — so the
target duration is UNKNOWN on both sides. That is a fact about the source, not a gap in the grab:
the property exists, its instance value is inherited from the class default object, which is in
`BmGame.upk`, not in the three Batmobile packages.

`RBatmobileEMPMissile` carries the lock and the projectile split (same file):

| member | offset | value |
|---|---:|---|
| `LockOnTime` | 2540 | (instance) |
| `MissileLockOnDuration` | 2560 | **2.0** |
| `CivilianMissileLockOnDuration` | 2564 | **1.0** |
| `MaxDamageAngle` / `AngleDamageFactor` | 2544 / 2556 | (instance) |
| `ProjectileForCarsArchetype` | 2492 | `RBatmobileMissile Batmobile_EMPMissile_Projectile_ForCars` |
| `LauncherAnimNodeName` | 2588 | `PursuitMissileAnim` |
| `ExplosionEvent` / `UntagWarningEvent` | 2500 / 2508 | AkEvents |

So the BmAK behaviour to reproduce is: **lock 2.0 s (1.0 s civilian) → fire → EMP missile → burst →
enemy vehicle disabled for `DisableEnemyDuration`**, with `EMPImpulse`/`EMPVehicleImpulse` shoving
the target. None of the three disable-side numbers (duration, impulse, power-level charge) has a
decoded value.

## 2. JC3 candidate 1 — "engine kill on damage": torque is floored, never zero

| member | type | fleet range | donor | what it can do |
|---|---|---|---|---|
| `LandEngine.engine_max_damage_torque` | float | **0.25 .. 0.75** (med 0.75, n=145) | 0.75 | torque multiplier at max engine damage |
| `LandEngine.engine_damage_noise_scale` | float | 1 .. 2 | 1 | audio only |
| `LandEngine.min_rpm` / `max_rpm` / `optimal_rpm` | float | 250..3500 / 2000..1e7 / 1100..9000 | 1000 / 7300 / 5000 | rpm band |
| `VehicleCommon.damage_from_parts[].damage_ratio_from_broken_off` | float | 1 .. 1 (n=3016) | 1 | a broken part feeds damage to the vehicle |
| `…damage_ratio_from_damaged` / `…_from_loose` | float | 0 .. 0 / 0 .. 0.95 | 0 / 0 | idem |
| `VehicleParts.parts[].should_break`, `break_parts_when_broken[]`, `meshswap_parts_when_broken[]` | flags/arrays | — | — | part destruction, not engine state |

`engine_max_damage_torque` is the whole "damaged engine" model, and **no vehicle in the fleet uses
0**: the floor is a quarter to three quarters of torque. A destroyed engine part therefore still
drives, and `damage_from_parts` routes the loss to the vehicle's health (`damage_ratio_from_broken_off`
= 1 on every row), not to a stall. **No module member turns the engine off** (see §6).

## 3. JC3 candidate 2 — the stalled-engine state in `vehicle_common` (the closest thing in data)

All 232 vehicle entities point their `VehicleCommon` module at one shared file,
`editor/entities/jc_vehicles/00_shared/modules/vehicle_common.vmodc` (`WATER.md` §7):

| member | value (all entities) |
|---|---|
| `car_common.engine_shut_down_delay_s` | **30** |
| `boat_common` / `helicopter_common` / `motorbike_common` / `plane_common.engine_shut_down_delay_s` | **5** each |
| `vehicle_damage.min_water_entry_ms` | **10** |
| `vehicle_damage.fatal_water_entry_ms` | **20** |
| `vehicle_damage.min_water_entry_floating_ms` | **20** |
| `vehicle_damage.fatal_water_entry_floating_ms` | **50** |
| `vehicle_damage.fire_spreading_speed_ms` | 1.5 |
| `vehicle_damage.in_air_vulnerability_duration` | 2 |

This **is** a stalled-engine state — the engine shuts down after a water entry, 30 s for cars — and
it is the only engine-off timer in any module. Its trigger is water, per vehicle class, and it is
**not reachable from a weapon, a pulse or another entity's data**: no member takes a trigger, and no
vehicle overrides it. The unit behind the `_ms` names is not decoded (`WATER.md` §7: 10/20 ms is too
short to be a drown timer, so the suffix is the only evidence).

## 4. JC3 candidate 3 — electrical / shock damage: the channel exists, nothing names it

`VehicleDamage` carries eight armour channels; the electric one is real and tuned:

| member | type | fleet range | pairs | build (test-091) |
|---|---|---|---|---|
| `electricity_armor` | int32 | **-1 .. 0** (med 0, n=233) | `0@0` ×192, `-1@100` ×41 | **-1** |
| `electricity_armor_strength` | float32 | 0 .. 100 | — | **100** |
| `grapple_pull_armor(_strength)` | int32/float | same shape | `0@0` ×192, `-1@100` ×41 | -1 / 100 |

Two facts keep this from being the EMP carrier:

1. **No weapon tune names a damage type** (`DAMAGE_MODEL.md` §3: across 1,515 member rows of 9
   decoded weapon tunes, 0 members mention a channel, heavy or penetration). Whether a `CEMPWeapon`
   hit arrives on `electricity`, `explosion` or `bullet` is UNKNOWN.
2. `-1` in the `*_armor` slot is a fleet convention shared by `electricity` and `grapple_pull` on the
   same 41 vehicles, so it does not mark EMP-hardened vehicles; it marks a pair of channels that
   are switched off.

The build already ships `-1 @ 100`, i.e. the strongest shipped value. Nothing in the data makes a
vehicle *stop* on that channel.

## 5. JC3 candidate 4 — the EMP weapon class and the Bavarium vocabulary

`CEMPWeapon` is a real engine class (`JustCause3.exe` RTTI `.?AVCEMPWeapon@@` @0x2D6E058,
`CGameObjectCreator<CEMPWeapon>` @0x23EFF40-ish, name string @0x23E9428) and ships in two files
(`EMP.md` §6):

| | `w702_emp` | `w503_turret_emp` |
|---|---|---|
| kind | handheld | static turret |
| weapon id / type | 702 / **6** | 503 / **2** |
| fire point | `FirePosition` (0, 0.13, −0.69) | `fire_position_1` (0, 3.762, −9.708) |
| components | 3 × `CBarrelSpinWeaponComponent`, pickup, wall penetration | `CTurretWeaponComponent` |
| tune | `w702_emp.wtunec` (stock `fow_weapon`) | `w503_turret_emp.wtunec` (stock) |
| damage / range | **500 / 50 m** | **500 / 750 m** |
| EMP field in the tune | **none** | **none** |

So the EMP behaviour is keyed entirely off the class in code, not off any tune value — the same
shape as `invulnerable` on the entity root (`DAMAGE_MECHANISMS.md` §1). No vehicle in the fleet
carries a `CEMPWeapon`: the 88 vehicle weapon components in `WEAPON_WIRING` include none.

The Bavarium/DLC side is vocabulary, not a vehicle mechanic: `BavariumShield` is a render block and
material (`CRenderBlockBavariumShield`, `m_BavariumShieldActive`), the DLC3 **mech** owns the EMP
*state* strings (`enemy.mech.exit_emp_state` @0x24D5238, `dlc3.electrical_damage_hud.on/off`
@0x2468B48/0x2468B28, `dlc3.electrical_warning_hud.on/off`, `UpdateElectricityWarning` @0x24AFFE8,
`Electricity` @0x2443D00). That is the player-facing EMP *status* UI — evidence the engine models
"a vehicle/mech that is EMP-disabled", and the only shipped place that state is surfaced.

## 6. JC3 candidate 5 — the state setter: `is_disabled_by_emp` exists, nothing writes it

The executable's vehicle-variable vocabulary contains the state itself:

```
0x24E9FC0 engine_real_load        0x24EA040 rear_left_suspension_length
0x24E9FD8 is_hide_character_weapon_set   0x24EA060 main_rotor_efficiency
0x24EA010 elevon_right_T          0x24EA078 can_fly
0x24EA020 angular_velocity_yaw_rads      0x24EA080 is_disabled_by_emp   <-- here
0x24EA040 rear_left_suspension_length    0x24EA098 flat_trajectory_curvature
0x24EA0B8 is_in_water             0x24EA0F0 …
```

and in the wider run: `engine_damage`, `engine_torque_max`, `vehicle_burning`, `is_frozen`,
`sinking_progress`, `health_norm`, `named…` — i.e. it is one of the per-vehicle values the engine
tracks and the value-driven-effect / HUD systems can read. **But it is not bound by any shipped
asset**:

| measurement | result |
|---|---|
| literal `is_disabled_by_emp` in **1,941** `.ee`/`.epe`/`.vmodc`/`.afsmb`/`.asb` entries (**3,978,089,026 B**) | **0** |
| Jenkins hash `0x0A6B5E46` (LE) in **1,307** `.ee`/`.epe` entries (**3,959,382,417 B**; an `.epe` stores property names as hashes) | **0** |
| control `invulnerable` (hash `0xAF4406FB`, proven live at `epe+1163`) | **289** entries |
| control `is_in_water` (hash `0x0A011C18`) | **160** entries |
| member names matching `emp|disab|stall|immobil` in `VOCABULARY.md` (52 module types, **1,421** members) | **0** |

Re-derivable: `python Tools/scripts/t_md2_emp_state.py --check` →
`PASS: … 1941 entries / 3978089026 B; controls hit; is_disabled_by_emp 0 literal / 0 hash`
(`Research/JC3Grab/EMP_DISABLE.json`).

**Caveat, stated because it matters.** A string in the vocabulary block is not proof that code reads
it: `ARMOR_STEP.md` §2 measured exactly this for the 473 ADF member names — 0 instructions and 0
pointers address them. The same test has not been run on the vehicle-variable block, so "the engine
reads `is_disabled_by_emp` by name/hash" is **UNKNOWN**; what is proven is (a) the name is engine
vocabulary, (b) no asset binds it. The state is set, if at all, by native code in the `CEMPWeapon`
hit path.

## 7. The chain, and the missing link

What the files support, end to end:

```
BmAK  RBatmobileEMP (Range, DisableEnemyDuration, EMPImpulse …)          <- what to build
        |                                                              duration value UNKNOWN
        v
JC3   CForcePulse "EMP"  SettingsFile = truck_emp.ftune  world = (0, 2.0356, 0.6992)
        |               8 numbers: Player 100 / r25 / 1 / 1 · AI 100 / r25 / 1 / 1
        v
      ForcePulseSettings -> explosion/hit of the victim vehicle
        |
        +--> VehicleDamage  max_health 500..4000 (build 2000), explosion_armor 0..250@0..100
        |    electricity_armor -1..0 @ 0..100      -> health loss only, no state
        +--> VehicleParts.parts[].damage_type -> part damage -> damage_from_parts (ratio 1)
        |                                          -> health loss only, no stall
        +--> LandEngine.engine_max_damage_torque 0.25..0.75  -> torque floor, never 0
        X    is_disabled_by_emp ....... exists in the engine, 0 data bindings   <-- MISSING LINK
```

and the two ways to reach the state, neither decidable from data:

```
(a) CEMPWeapon (w702_emp / w503_turret_emp)  --class-keyed-->  native hit path --> is_disabled_by_emp
      gap: 0 of 88 vehicle weapon components is a CEMPWeapon; does the engine accept one in a
           car's weapon slot?  UNKNOWN -> probe
(b) CForcePulse "EMP"  --unowned, no pointer-->  ????  --> is_disabled_by_emp
      gap: 14 unowned pulses in the fleet; the firing moment of all 307 pulses is UNKNOWN
           (FORCEPULSE.md §4.3). The pulse can be copied; nothing in the files fires it.
```

The pulse's only EMP-specific data, for build (b): the three flags that differ from the plain car
blast form a combination **unique among all 307 pulses** — `id:4912FC04=0`, `id:AE6F7EFF=1`,
`id:CF4F7880=1` (the other combinations: `1,0,0` ×278, `0,0,0` ×16, `1,0,1` ×12). Around them:
`id:060AAA81=20`, `id:24872388=100`, `id:530046B3=10`, `id:57F1B4E1=0.1`, `id:9865E7F2=100`,
`id:A1B0DAF9=2`, `id:F39EC6EA=0.1`, `id:D3DDD766`→`CMaterialEffectTable emp_flatbed_table`
(`explosion_emp_flatbed.effc`), `id:06A05F33`→unresolved id. Whether those flags are the disable is
**UNKNOWN**; they are the only data-side candidates, and they are free to ship.

## 8. Closest system and gap, per STAGES.md

| stage | row | closest JC3 system (member paths + values) | gap the build fills |
|---|---|---|---|
| TRANSLATE | **T-MD2** disable | `CEMPWeapon` — class @ exe RTTI `.?AVCEMPWeapon@@`, shipped as `w702_emp` (type 6, damage 500, range 50 m, 3 barrel-spin components) and `w503_turret_emp` (type 2, 500, 750 m); disable duration is native | mount a cloned `CEMPWeapon` on the Batmobile's second driver slot `id:00568A74` (the slot T-WP2 gives the Vulcan) or a private copy of `w702_emp.wtunec`; **probe whether the engine accepts the class on a vehicle** — the one thing data cannot answer |
| TRANSLATE | **T-WP5** burst | entity `CForcePulse` + `truck_emp.ftune` (100/25/1/1) + the unique flag triple `4912FC04=0, AE6F7EFF=1, CF4F7880=1`, position `(0, 2.0356, 0.6992)` on the truck (chassis centre for the car) | the **trigger**: the pulse has no owner and no pointer; copy it, then fire it from the `CEMPWeapon` path or from a graph script whose bytecode is not decoded — do not invent a trigger |
| TRANSLATE | **T-WP4** missile | `w618_sportsmuscle_missile` clone (blast `w618_sportsmuscle_missile.ftune` 1100/8 m player, 500/8 m AI) + `RBatmobileEMPMissile` lock values (`MissileLockOnDuration` 2.0, `Civilian…` 1.0) | the missile is flyable today; its **impact must fire the disable**, which is T-MD2's gap — same link |
| BUILD | B-xx (new) | the above | one probe build: stock car + cloned `w702_emp` on the second slot, `truck_emp.ftune` pulse at chassis centre, flag triple as shipped |

**Probe cards (phase Q; the ban in `tmp/freebuff/APPROVED_Q.txt` governs when they may run):**

* `Q-EMP-1` — **does the engine's own `CEMPWeapon` disable a car?** Spawn a stock civilian car, give
  Rico `w702_emp` (shipped, base game), fire one burst at it. Record: does the engine die/stall, for
  how long (a stopwatch at 1 s resolution), does the HUD show the `dlc3.electrical_*` warning, does it
  restart or stay dead. This measures the native duration that `DisableEnemyDuration` would carry.
  Expected: if the state is class-keyed, the car stops; if not, only 500 damage lands.
* `Q-EMP-2` — **does the pulse alone disable, or only its weapon?** Spawn the EMP truck
  (`rebel_emp_01`), park a stock car within 25 m, press use-item on the flatbed. Record: car stalls
  (pulse flags are the disable) vs car takes 100 damage and drives on (flags are only damage shape).
  This is the cheapest possible test of the one unique data marker.
* `Q-EMP-3` — **is a `CEMPWeapon` accepted on a car?** Install the probe build and fire the second
  slot at a stock car. Expected if accepted: same stall as `Q-EMP-1`, with the Batmobile as the
  source. If the slot silently does nothing, the class is not vehicle-mountable and the omission is
  recorded as a code-side gap, not a value gap.
* `Q-EMP-4` — **duration on the Batmobile's own target**: repeat `Q-EMP-1` at 0 s / 5 s / 15 s after
  the hit to bracket the state's length; that bracket is the only source for `DisableEnemyDuration`.

## 9. What would settle each UNKNOWN

| UNKNOWN | what would settle it |
|---|---|
| does code read `is_disabled_by_emp`? | `ARMOR_STEP.md`'s method (instruction scan + pointer scan) applied to the vehicle-variable name block at 0x24E9F40..0x24EA210; 0 handles would make the variable HUD/vocabulary-only |
| the disable's duration in BmAK | the `RBatmobileEMP` **class default object** in `BmGame.upk` (`CDO_PAYLOADS.md` tooling); the three Batmobile packages only carry the instance |
| which damage channel a `CEMPWeapon` hit uses | one in-game hit on a vehicle with a known channel split (the medium tank: `bullet` 5000@99, `explosion` 250@50, `electricity` −1@100) — a tank that shrugs off bullets but reacts to the EMP puts it on `electricity`/`explosion` |
| what the three pulse flags mean | `Q-EMP-2`; if the pulse alone stalls, the flags are the switch, and `4912FC04=0/ AE6F7EFF=1 / CF4F7880=1` becomes the build value |
| whether a pulse can be fired from a graph script | decode `CGraphScriptGameObject.GraphScript` bytecode (13 entities; the mm340 `BOMB_JEEP` rule is the only shipped case that points at a pulse) |

## 10. Evidence and reproduce

| evidence | path |
|---|---|
| pulse members, tunes, owners, unowned pulses | `Research/JC3Grab/FORCEPULSE.md` §1/§3/§4.3, `FORCEPULSE.json` |
| EMP truck device, tune, weapons, copy list | `Research/JC3Grab/EMP.md` §1/§2/§6/§7 |
| water/stall constants | `Research/JC3Grab/WATER.md` §7 |
| module members (LandEngine, VehicleCommon, VehicleDamage, VehicleParts) | `Research/JC3Grab/VOCABULARY.md` |
| channel values, fleet ranges, weapon arms | `Research/JC3Grab/DAMAGE_MODEL.md` §1/§3/§7 |
| `invulnerable` / level switch method | `Research/JC3Grab/DAMAGE_MECHANISMS.md` §1/§3 |
| ADF name blocks are inert in code (caveat) | `Research/JC3Grab/ARMOR_STEP.md` §2 |
| BmAK EMP members + offsets | `Research/BatmobileGrab/BMSDK_OFFSETS.json` (`RBatmobileEMP`, `RBatmobileEMPMissile`) |
| BmAK EMP serialised tags | `Research/BatmobileGrab/objects.jsonl` |
| the scan (this report's numbers) | `Research/JC3Grab/EMP_DISABLE.json`, `Tools/scripts/t_md2_emp_state.py` |

```bash
python Tools/scripts/t_md2_emp_state.py --write    # re-reads exe + archives, rewrites the JSON
python Tools/scripts/t_md2_emp_state.py --check    # exits 1 on any drift; prints the PASS line above
python Tools/scripts/jc3emp.py --check            # the G2-16 EMP card still re-derives
```

**Limits.** Static only: no game launched, nothing installed, no save touched, no archive written.
The scan covers the entries `INDEX.jsonl` names (1,941 of 81,952); DLC content without a filelist is
named only through the JCMR dictionary, so a DLC asset that binds `is_disabled_by_emp` would be
missed — the DLC3 mech is the likeliest such asset and it is **not** in the scanned set beyond the
`dlc/mech_land_assault` vehicle entries that are. A 4-byte hash can collide (expected ~1 hit per 4 GB
of random data); the `electricity_armor` hash hit (1) is therefore reported as a possible collision,
not as a binding. The `-1` armour convention is inferred from the fleet's two-channel pairing, not
from a decoded semantic. And the disable is behaviour: the only instrument that can read
`is_disabled_by_emp` is the game, which is why §8 ends in probes, not values.
