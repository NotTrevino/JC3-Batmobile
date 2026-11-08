# JC3 vehicle-weapon HUD API (HUD-2, WPN-12)

G2-25. **Answer: JC3's vehicle-weapon HUD is `2` slots, an optional cooldown loader, and a reticle; it has no heat bar and one lock-on marker.**

`InitVehicleWeapons` takes **9 arguments** and `UpdateVehicleWeapons` **6**; between them they carry weapon id, name, infinite-ammo flag, magazine ammo, magazine size, inventory ammo and a `0..1` cooldown plus an overcharge flag. Neither has a heat argument and neither body mentions heat: **WPN-12's Vulcan heat bar is a stated absence on both sides** - JC3's movie "heat" is the 11-state police wanted level, and the Batmobile's heat is a weapon-entity script variable with no `UC_*` setter.

The lock-on is **one POI**, `POI_TYPE_LOCK_ON_TARGET = 21`, drawn by `hud_code/poi.as` as a single rotating reticle (1.5 s per turn); the flashing `MCI_missile_locked` is a different, *incoming*-missile warning. The `VehicleMissileTarget*` box family (6 kinds) and the hit/failure events have no JC3 element. **What calls the API from the entity side is native code**: the only call sites in all 260 scripts are 2 demo calls inside `TestConstructor`, so the weapon-id -> HUD bridge stays `UNKNOWN`.

Sources: the decompiled `ui/hud.gfx` export (G2-19) - `260` AS3 scripts, `hud.as` 11295 lines - plus `INDEX.jsonl` (icon census), `WEAPONS.jsonl` / `WEAPON_WIRING.jsonl` (the three lock-on missiles), `HUD_INTERFACES.json` + `HUD.md` (the BmAK half of WPN-12) and the card's own WPN-12 and T-HUD5 rows. Nothing here comes from a wiki, and no archive is opened: only decoded text.

## 1. `InitVehicleWeapons` - the arguments

```
public function InitVehicleWeapons(slot_index:int, weapon_id:int, weapon_name:String, infiniteAmmo:Boolean = true, magazine_ammo:int = -1, magazine_size:int = -1, inventory_ammo:int = -1, weapon_cooldown:Number = -1, is_overcharged:Boolean = false) : void
```

| # | argument | type | default | what the body does with it |
|---|---|---|---|---|
| 0 | `slot_index` | `int` | `-` | indexes `m_WeaponsArray` / `m_WeaponsDataArray`; no range check |
| 1 | `weapon_id` | `int` | `-` | stored, then the icon is loaded from it (see §6) |
| 2 | `weapon_name` | `String` | `-` | `TXT_name.text` - the label under the slot |
| 3 | `infiniteAmmo` | `Boolean` | `true` | branches the whole ammo block: true hides the counters and shows `MCI_inventory_infinity`, false shows magazine/inventory text and frames `MCI_bullet_bar_anim` at `65 * ammo / size` |
| 4 | `magazine_ammo` | `int` | `-1` | stored as `m_MagazineAmmo`; only used for the initial bullet-bar frame |
| 5 | `magazine_size` | `int` | `-1` | stored as `m_MagazineSize`; the denominator of the bar fraction |
| 6 | `inventory_ammo` | `int` | `-1` | stored as `m_TotalInventoryAmmo`; `TXT_selected_inventory_ammo.text` |
| 7 | `weapon_cooldown` | `Number` | `-1` | `-1` hides `MCI_radial_loader_cooldown`; otherwise `SetCooldownRotation(slot, value)` (§3) |
| 8 | `is_overcharged` | `Boolean` | `false` | `AnimateOvercharged(slot, flag)` - bullet-bar alpha + the ready sound (§3) |

`slot_index` is not validated: the body indexes two-element arrays directly. The body is 34 lines and writes 6 fields of the per-slot data object: `m_HasInfiniteAmmo`, `m_MagazineAmmo`, `m_MagazineSize`, `m_TotalInventoryAmmo`, `m_WeaponId`, `m_WeaponName`.

## 2. `UpdateVehicleWeapons` - the arguments

```
public function UpdateVehicleWeapons(slot_index:int, new_magazine_ammo_amount:int, total_ammo:int, is_low_ammo:Boolean, weapon_cooldown:Number = -1, is_overcharged:Boolean = false) : void
```

| # | argument | type | default | what the body does with it |
|---|---|---|---|---|
| 0 | `slot_index` | `int` | `-` | the slot to update |
| 1 | `new_magazine_ammo_amount` | `int` | `-` | `m_MagazineAmmo`; **`<= 0` returns early**, before any drawing |
| 2 | `total_ammo` | `int` | `-` | `m_TotalInventoryAmmo`; written to the text only when `>= 0` |
| 3 | `is_low_ammo` | `Boolean` | `-` | pulses `MCI_bullet_bar` alpha to 0.2 every 0.25 s, else `ClearTween` |
| 4 | `weapon_cooldown` | `Number` | `-1` | only when `!= -1`: `SetCooldownRotation` + `AnimateOvercharged` |
| 5 | `is_overcharged` | `Boolean` | `false` | the overcharge tint/sound, gated behind the cooldown argument |

Note the asymmetry: init sends the *name* and the *icon*, update never does - a vehicle that changes weapon has to call `InitVehicleWeapons` again, and the icon request is skipped when the id did not change.

## 3. Slots, cooldown and overcharge

The slot array is built in `VehicleConstructor`:

```
this.m_WeaponsArray = new Array(this.MCI_safe_area_bottom_right.MCI_vehicle_weapons0,this.MCI_safe_area_bottom_right.MCI_vehicle_weapons1);
```

So the vehicle HUD has **2 slots** (`MCI_vehicle_weapons0, MCI_vehicle_weapons1`), indexed `0` = `EVEHICLE_WEAPON_SLOT_MAIN` and `1` = `EVEHICLE_WEAPON_SLOT_ALTERNATIVE`. Do not confuse this with `E_NUM_WEAPON_SLOTS = 7`, which is the **on-foot** weapon wheel: the same `hud.as` carries both and the vehicle arrays are hard-sized to 2.

Each slot clip carries 7 widgets the two functions touch (`MCI_bullet_bar`, `MCI_inventory_infinity`, `MCI_selected_weapon_icon`, `TXT_bullet_ammo`, `TXT_name`, `TXT_selected_inventory_ammo`, `TXT_slash_mark`) and 3 parts of its bullet bar (`MCI_bullet_bar_anim`, `MCI_radial_loader_cooldown`, `alpha`).

| mechanism | code | value |
|---|---|---|
| cooldown -> rotation | `SetCooldownRotation` | `rot = weapon_cooldown * 360`, `MCI_mask_0_50.rotation = min(rot, 180)`, `MCI_mask_50_100.rotation = max(rot - 180, 0)` |
| loader visibility | `InitVehicleWeapons` | `MCI_radial_loader_cooldown.visible = weapon_cooldown != -1` |
| overcharged | `AnimateOvercharged` | bullet bar alpha 0.7 while overcharged; pulsing radial loader; `PlaySound('dlc_wingsuit_weapon_ready')` on release |
| state kept | `m_IsOverchargedArray` | two booleans, one per slot |

`weapon_cooldown` is a **fraction, not a state**: `1` is a full ring, `-1` means "this slot has no cooldown display at all". The Batmobile's `UC_SetCannonCoolDown` is the opposite shape (see §7).

## 4. `UpdateWeaponReticle` - shapes, look and size

```
public function UpdateWeaponReticle(show:Boolean, weapons_look:int, reticle_size:Number, reticle_shape:int) : void
```

| shape | id | size rig |
|---|---|---|
| `E_RETICLE_SINGLE_SHOT` | 0 | cross: `RETICLE_CROSS_WIDTH_MIN + size * (MAX - MIN)` |
| `E_RETICLE_CIRCLE` | 1 | circle: `RETICLE_CIRCLE_WIDTH_MIN .. MAX` |
| `E_RETICLE_DOT` | 2 | no size rig |
| `E_RETICLE_NONE` | 3 | hidden, and it hides `MCI_inflict_damage` |
| `E_RETICLE_AUTO` | 4 | cross (same rig) |
| `E_RETICLE_WINGSUIT` | 5 | no size rig |
| `E_RETICLE_ROCKET` | 6 | rocket: `RETICLE_ROCKET_WIDTH_MIN .. MAX` |
| `E_RETICLE_GRENADE_LAUNCHER` | 7 | no size rig |
| `E_RETICLE_CANNON` | 8 | no size rig |
| `E_RETICLE_FLAK` | 9 | cross rig via `MCI_cross.*` |
| `E_RETICLE_WINGSUIT_WEAPONIZED` | 10 | no size rig |
| `E_RETICLE_MECH_CANNON` | 11 | no size rig |
| `E_RETICLE_MECH_MINIGUN` | 12 | no size rig |
| `E_RETICLE_POWERCORE` | 13 | no size rig |

| look state | id | effect |
|---|---|---|
| `ECrosshairLook_InRangeTargetNeutral` | 0 | non-hostile colour |
| `ECrosshairLook_InRangeTargetAllied` | 1 | friendly colour |
| `ECrosshairLook_InRangeTargetHostile` | 2 | hostile colour |
| `ECrosshairLook_InRangeNoTarget` | 3 | non-hostile colour |
| `ECrosshairLook_OutOfRange` | 4 | non-hostile colour **and** alpha 0.4 |

`show` toggles `m_WeaponReticleGroup.visible`. Shape `3` hides `MCI_inflict_damage`; for shapes 8/11/12 (cannon, mech cannon, mech minigun) the marker sits at y = -111, otherwise at y = -21. Widths come from 17 `RETICLE_*` constants. The size switch has 14 `case` labels but only 5 of them compute a width (`E_RETICLE_AUTO`, `E_RETICLE_CIRCLE`, `E_RETICLE_FLAK`, `E_RETICLE_ROCKET`, `E_RETICLE_SINGLE_SHOT`); the other 9 fall through with no size change.

This is the **player weapon** reticle. A vehicle's own reticle is not a shape id in this enum: the vehicle cluster mounts `MCI_vehicle*` clips, and the Batmobile's heavy reticle has to be expressed as one of these shapes plus `weapons_look` colours. Which shape the game picks for a vehicle cannon is `UNKNOWN` (native).

## 5. Lock-on: one POI, and an incoming warning

`hud.as` declares 32 `POI_TYPE_*` constants and builds any of them with `CreatePoi(type, use_progress_bar, is_minor, label)`; `hud_code/poi.as` switches on the type to pick the icon. Exactly one type is a lock-on reticle:

| what | value | evidence |
|---|---|---|
| lock-on type | `POI_TYPE_LOCK_ON_TARGET = 21` | `hud.as` constant + `poi.as` case |
| icon | `MCI_icon_and_label.MCI_icon.MCI_lock_on.MCI_reticle` | `poi.as` case 21 |
| animation | `TweenRotation(ret, 1.5, 360, TM_LINEAR, TR_LOOP)` - one turn every 1.5 s | `LOCK_ON_TARGET_ROTATION_TIME` |
| progress bar | `m_HasProgressBar = false` | same case |
| incoming warning | `MCI_safe_area_bottom_middle.MCI_missile_locked`, flashing every 0.5 s | `MISSILE_LOCKED_TIMER`, `FlashMissileLocked` |
| warning API | `ShowMissileLocked()` / `HideMissileLocked()`, 0 / 0 call sites in the movie | grep of all 260 scripts |
| lock-on created by the movie | no - 0 `CreatePoi(POI_TYPE_LOCK_ON_TARGET, ...)` calls | grep |

**These are two different instruments.** `MCI_missile_locked` is the "a missile is locked on *you*" warning, blinking at half-second intervals; the rotating `POI_TYPE_LOCK_ON_TARGET` reticle is the marker on the thing *you* locked. The Batmobile's HUD needs both, and JC3 has exactly one of each.

### 5.1 The three lock-on missiles the card names

`w609`, `w612`, `w613` are the fleet's lock-on missiles. Their *"lock-on"* is a data fact with a name and an `AutoAim` tune, not a HUD member:

| weapon | class | chassis | binding | autoaim tune | damage | turning speed | loose-lock |
|---|---|---|---|---|---|---|---|
| `w609_fighterjet_missile_air_lockon` | `CRPGFireLeachWeapon` | 1 | secondary (id:00568A74) | `w609_fighterjet_missile_air_lockon_autoaim.wtune` | 1500 | 150 | 0 |
| `w612_fighterbomber_missile_air_lockon` | `CRPGFireLeachWeapon` | 1 | - | `w612_fighterbomber_missile_air_lockon_autoaim.wtune` | 1500 | 300 | 0 |
| `w613_fighterbomber_missile_ground_lockon` | `CMissileWeaponBase` | 1 | secondary (id:00568A74) | `autoaim_w613_bombs.wtune` | 1500 | 0 | 0 |

`OnFoot` profile of the same tunes - the envelope a lock is acquired in:

| weapon | new-target angle | held-target angle | min dist | max dist | can target chars/vehicles/objects |
|---|---|---|---|---|---|
| `w609` | 0.085 | 0.3 | 25 | 750 | 0 / 1 / 1 |
| `w612` | 1.4 | 1.4 | 5 | 750 | 0 / 1 / 1 |
| `w613` | 0.12 | 0.15 | 15 | -1 | 0 / 0 / 0 |

| weapon | components | magazine | burst | fire rate | max range |
|---|---|---|---|---|---|
| `w609` | CLaserBeamWeaponComponent | 8 | 1 | 0.2 | 750 |
| `w612` | (none) | 2 | 1 | 0.5 | 300 |
| `w613` | CLightWeaponComponent | 6 | 6 | 0.2 | 300 |

Three details in that table are traps and are reported as read: `w609`'s only component is `CLaserBeamWeaponComponent` (the fighterjet's laser/tracer component sits on the missile object - a component's name is not evidence of what the weapon does, R5); `w612` has none and is bound to **no driver slot** (G2-11's unbound list); `w613` carries only its `warning_light`. Mode of acquisition is therefore not carried by a component, unlike the no-lockon `w611`, which is the one that carries `CAimPOIWeaponComponent`.

Read the table twice: `w609` is an air-to-air missile (angles in fractions of a turn, vehicles + rigid objects, 750 m), `w612` is looser still, and `w613` - the "ground lockon" - **targets nothing**: `CanTargetCharacters`/`Vehicles`/`RigidObjects` are all 0, `MaxAimDistance` is -1 and `missile_turning_speed` is 0, so it is an unguided bomb with a ground reticle. Its ES name promises a lock the data does not implement.

**The link from an `AutoAim` tune to `POI_TYPE_LOCK_ON_TARGET` is not in any file.** The tunes say what can be acquired and at what angle; the movie says a POI of type 21 draws a rotating reticle. Nothing connects them, no ship script creates the POI, and `CAimPOIWeaponComponent` (11 entity builds, e.g. on `w611`, the *no-lockon* missile) is a component whose name says POI but whose props are only `id:2D0B3C09 = 100` and a world position. Whether the engine paints `POI_TYPE_LOCK_ON_TARGET` from `AutoAim` state: `UNKNOWN` - native. That gap is why §7's lock-on row is `partial`, not `map`.

## 6. How the entity feeds the HUD: the weapon id is the icon

```
weapon_icon_name = weapon_id.toString();
return "textures/ui/weapon_icons/" + weapon_icon_name + ".ddsc";
```

`GetWeaponIconName(weapon_id, low_res)` appends `_sm.ddsc` when `low_res_image` is set; `weapon_icon_type.LoadIcon` drops the icon entirely for ids -1 and 0. So the file name is **the weapon id alone** - no name, no category, no hash.

`INDEX.jsonl` carries **69 distinct icon ids** in 110 `textures/ui/weapon_icons/*.ddsc` files (69 full-res plus `_sm` low-res twins). The fleet's 88 wired weapon components use 23 distinct ids; 22 of them have an icon:

- ids with an icon: 206, 601, 602, 603, 604, 605, 606, 607, 608, 609, 610, 611, 612, 613, 615, 616, 617, 618, 619, 620, 621, 622
- **without an icon: 614**; id `614` belongs to `w614_monorailmissilecar_missile`

That gap is drawn from the files, not a guess: the monorail's missile component sets a `weapon_id` whose icon was never shipped, so any vehicle that reuses it shows a slot with no icon. The Batmobile must not reuse that id; the ids that do resolve are the usable set.

| weapon | id | icon file present |
|---|---|---|
| `w609_fighterjet_missile_air_lockon` | 609 | yes (`textures/ui/weapon_icons/609.ddsc`) |
| `w612_fighterbomber_missile_air_lockon` | 612 | yes (`textures/ui/weapon_icons/612.ddsc`) |
| `w613_fighterbomber_missile_ground_lockon` | 613 | yes (`textures/ui/weapon_icons/613.ddsc`) |

The chain a modder can rely on is therefore: **weapon component's `weapon_id` property -> `weapon_id.toString()` -> `textures/ui/weapon_icons/<id>.ddsc`**, and `InitVehicleWeapons`' third argument is the *label*, not the icon. What is missing is the caller that reads the component and calls the movie (next section).

## 7. WPN-12, element by element

The card's own row: *HUD: weapon slots, reticle, cannon cooldown, Vulcan heat, missile lock | `HUD_INTERFACES.json` (`UC_SetCannonCoolDown` …) | `hud.gfx` `InitVehicleWeapons`/`UpdateVehicleWeapons` (T-HUD5)*

| element | BmAK source | JC3 element | disposition | limit |
|---|---|---|---|---|
| **weapon slots** | HudModuleBatmobile.UC_SetPrimaryWeapon(name), UC_SetSecondaryWeapon(name, b, b), UC_SetSpecialWeapons(3 x state); HudModuleTargets reacts to Weapon/WeaponHit/WeaponFailure | 2 slots (MCI_vehicle_weapons0, MCI_vehicle_weapons1) via InitVehicleWeapons(slot_index 0..1) / ShowVehicleSlotAction / HideVehicleSlotAction; hidden by HideVehicleUi | map | 2 slots total: the Batmobile's primary + secondary weapon map, the special-weapon states have no JC3 member |
| **reticle** | HudModuleBatmobile battle-mode reticle (recticuleHeavy) + UC_SetCannonCoolDown states Ready/Blank/PreReady*; UC_SetMachineGunAccuracyFrame | UpdateWeaponReticle(show, weapons_look, reticle_size, reticle_shape): 14 shapes (E_RETICLE_NONE 3 .. E_RETICLE_POWERCORE 13), 5 look states, size 5..30 px, cross/rocket/circle rigs | map (shape id UNKNOWN) | which shape id the Batmobile's heavy reticle should use is not in the files; E_RETICLE_CANNON exists but nothing maps it to a vehicle cannon |
| **cannon cooldown** | UC_SetCannonCoolDown(int in 0…4) -> reticle Ready / Blank / PreReady* | weapon_cooldown in Init/UpdateVehicleWeapons (-1 = no loader), SetCooldownRotation 0..1 -> 360 deg over MCI_mask_0_50 + MCI_mask_50_100, AnimateOvercharged; is_overcharged sound 'dlc_wingsuit_weapon_ready' | map (0..1 replaces 5 states) | BmAK sends 5 categorical states, JC3 takes a 0..1 fraction: the 5 states have to be pinned to 5 fractions before the loader reproduces them |
| **Vulcan heat** | 2 script fields (HeatBarSize, HeatBarStart) on Batmobile_Cannon_V2; 0 of 252 UC_* setters contain 'heat' | 0 heat parameter in the vehicle-weapon API, 0 mention of heat in the bodies it drives; the movie's heat code is the 11-state police wanted level (hud_code/heat/) | stated absence (both sides) | JC3 shows ammo + a cooldown loader + an overcharge tint, never a heat bar; the Batmobile's heat is a weapon-entity script variable with no HUD setter, so no number or member carries WPN-12's heat bar |
| **missile lock** | HudModuleTargets: batmobile_lockon, batmobile_aim, missile_lockon_square_anim, 6 VehicleMissileTarget kinds (Invalid, bomb, emp, friend, multi, plain); UC_SetBatmobileWeapon(primary, b) / WeaponHit / WeaponFailure; radar side UC_SetLockonValue(value, kind) | one lock-on POI: POI_TYPE_LOCK_ON_TARGET = 21 -> MCI_icon.MCI_lock_on.MCI_reticle, rotated 360 deg every 1.5 s (hud_code/poi.as); separate incoming-missile warning MCI_missile_locked flashing at 0.5 s (ShowMissileLocked/HideMissileLocked, 0 movie callers) | partial: one lock-on marker, no target-kind family | JC3 has a single rotating lock-on icon and one incoming warning; the 6-kind missile box family, the aim box, per-target health and the hit/failure events have no JC3 element |

The BmAK side is `HudModuleBatmobile` (37 `UC_*` setters) and `HudModuleTargets` (16); across all modules there are 252 setters and **0 of them mention heat** - the heat bar is not an interface, it is the weapon entity's `HeatBarStart`/`HeatBarSize` script fields on `Batmobile_Cannon_V2` (4 rows in `MECHANICS.md`).

T-HUD5 (`Working/Translation/T6_HUD_CAMERA.md`) said this before the card ran:

```
| T-HUD5 | `UC_SetCannonCoolDown(0…4)`, heavy reticle, special weapon states | `InitVehicleWeapons` / `UpdateVehicleWeapons` (2 slots) | categorical | no weapon component on the mod | **blocked**: the HUD supports it, the entity does not | decoded | fire the cannon, reticle cooldown |
```

Its "2 slots" is now confirmed from the array itself, not from a summary; its "blocked: the HUD supports it, the entity does not" is unchanged by this card - the HUD side is decoded, the entity-side caller is native (`UNKNOWN`, §8).

**Result: all five elements have a JC3 element or a stated absence, and none of them is a silent gap.** Three map (slots, reticle, cooldown), one is a stated absence on both sides (heat), one is partial (lock-on: one marker where the Batmobile has a 6-kind family).

## 8. Who calls the API

| function | definition | call sites in the movie | where |
|---|---|---|---|
| `InitVehicleWeapons` | 1 | 2 | TestConstructor |
| `UpdateVehicleWeapons` | 1 | 0 | - |
| `UpdateWeaponReticle` | 1 | 0 | - |

- `hud.as:7535` in `TestConstructor` - `this.InitVehicleWeapons(0,141,"Panther",true,5,15,60);`
- `hud.as:7536` in `TestConstructor` - `this.InitVehicleWeapons(1,141,"Minigun",true,2,20,100);`

`UpdateWeaponReticle` has 0 call sites in the movie as well, and `ShowMissileLocked`/`HideMissileLocked` have none. These are **public** functions on the movie's document class: the game calls them from native code through the HUD interface, which is not in these files. So *who* feeds a vehicle's weapons to the HUD, and with what values, is `UNKNOWN` (R5: the behaviour is unproven until a drive proves it). What is proven is the shape of the call: a slot index, a weapon id, a label and a `0..1` cooldown.

## 9. Checks

| check | result |
|---|---|
| `python Tools/scripts/jc3hudwpn.py --check` | rebuilds both files from the same inputs and asserts every number above |
| scripts scanned | 260 `.as` under `hud\dec\scripts` |
| function signatures | `InitVehicleWeapons` 9 args, `UpdateVehicleWeapons` 6 args, parsed from the source, not typed |
| slot count | 2, from the `new Array(...)` line |
| icons | 69 ids in `INDEX.jsonl` |
| WPN-12 rows | 5 |

Every number in this page is regenerated by the script; none is typed by hand. Re-running `--write` after a change to the decompiled export or to the repo tables is the only way to edit it.
