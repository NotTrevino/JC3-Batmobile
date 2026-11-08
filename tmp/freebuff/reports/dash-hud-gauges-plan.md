# Dash HUD gauges — every gauge BmAK draws while driving, and the JC3 element/setter for each

**Question:** itemise every gauge the Batmobile HUD draws while driving (speed, boost, health,
ammo, selector) with position, colour and units; name the JC3 HUD movie element and the setter that
drives it; and where the JC3 element reads a different quantity, say what we feed it.

**Verdict.** The Batmobile module draws **five gauge families, but only two of the five the brief
names exist as gauges while driving**: the **afterburner bar (0…100, plus 2 upgrade badges)** and the
**health bar (proportion 0…1 + 5 armour tiers)**. **Speed is not drawn at all** (no movie, no setter:
the install's only speedometer is a native debug flag that is off in both configs). **Ammo is not
drawn as a number** — the cluster shows weapon *names*, three special-weapon *states* and a 5-state
cannon-cooldown reticle; the Vulcan heat bar exists only as two script fields on the weapon entity
and reaches no `UC_*` setter. **The mode selector is not drawn while driving either** —
`BattleAndZoomInterface.visible` is false in `DRIVE`, so the BATTLE/ZOOMED selector only appears
once you leave driving. Colour is **UNKNOWN for every gauge**: no record in the grab carries a
gauge colour, though `UC_SetColorTransform(a,b,c,d,e,*)` exists on both gauges' modules as a runtime
tint hook.

On the JC3 side the mapping is: boost → `MCI_nitro_meter` (`InitVehicleNitrous` /
`UpdateVehicleNitrous`, 0…1 recharge); health → the `MCI_vehicle` health paint (`hud_code/health/*`,
no public vehicle-health function in the movie — caller is native, **UNKNOWN**); ammo → the two
`MCI_vehicle_weapons0/1` slots (`InitVehicleWeapons` / `UpdateVehicleWeapons`); speed → `MCI_speedo`
(`InitPrimaryMeter` / `SetPrimaryMeterValue`), which we must **hide**, not feed; selector → **no JC3
element at all**.

Labels: **decoded** = read in the cited file at the cited field; **derived** = arithmetic or mapping
over decoded inputs; **UNKNOWN** = searched and absent, with where it would be settled.

---

## 1. What "while driving" means in this movie (decoded)

`Research/BatmobileGrab/HUD.md` §4: the Batmobile module is `HudModuleBatmobile.Image`, 51 frames,
30 fps, 1024×768 SWF surface on a 1024×720 module stage, document class `ModularHudBm3`, module
`ModuleStruct_Batmobile`.

* Main timeline labels: `DRIVE`, `BATTLE`, `ZOOMED`, plus
  `DRIVETOBATTLE`/`BATTLETODRIVE`/`BATTLETOZOOMED`/`ZOOMEDTOBATTLE`/`ZOOMEDTODRIVE`.
* `ModuleStruct_Batmobile.SetBattleAndZoomMode(battle, zoomed)` is the mode machine; it calls
  `BattleAndZoomInterface.gotoAndPlay(<from>TO<to>)`, **sets the interface visible outside `DRIVE`**,
  and entering battle forces the health bar visible with the `Delayed` intro.
* Boost has **no mode gate** (`Working/HUD/CLUSTER.md` §1); the health bar's transform never
  changes with the mode — only its visibility.

So in `DRIVE` the player sees: the afterburner bar (always), the health bar (only after damage, or
during its 2 s offscreen timer), the combo meter and XP bar if active — and **not** the mode
interface, **not** a speedometer, **not** an ammo counter.

---

## 2. The gauge table (position, colour, units, BmAK setter)

Positions are the authored 3-D transforms of the clips inside `HudMaster.LeftSideParent` /
`RightSideParent`, decoded from `HudModuleBatmobile`'s `AnimatorFactory3D` property arrays
(`Working/HUD/CLUSTER.md` §1, `tmp/freebuff/reports/G3-HUD-CLUSTER.md` §1). The screen estimate is
**derived** as `(512 + x, 384 + y)` from the movie's projection centre (512, 384) on the 1024×768
surface; the module stage is 1024×720.

| gauge | element (clip) | authored x, y, z | yaw | screen estimate | colour | units | BmAK setter |
|---|---|---|---:|---|---:|---|---|
| **Speed** | **none** — no clip, no setter | — | — | — | — | — | **none**: 0 of 252 setters are speed/rev/gear-shaped (`speedometer.movie_speed_setters = []`) |
| **Boost / afterburner** | `HudMaster.LeftSideParent.BoostMovie` (class `BoostGauge_344`) | **−452.867, 65.550, 24.110** | 26.0° | **(59.1, 449.6)** — left edge, lower half | **UNKNOWN** | **level 0…100** (int) + **upgradeLevel** 0…2 | `UC_SetBoostLevel(level:int, upgradeLevel:int)`, `UC_HideBoostGauge()`, `UC_ShowBoostUpgrade(name, name)` |
| ↳ boost fill | `BoostMovie.FillMovie` (102 frames) + `Cap` | local | — | inside the bar | UNKNOWN | `frame = level + 1`; fill scale-y **0.011 → 1.0**, bottom-anchored, **101 value steps** | same setter |
| ↳ boost badges | `BoostMovie.Background.Upgrade1`, `Upgrade2` | local **(−10.0, 96.3)** and **(−10.5, 100.6)** | — | inside the bar | UNKNOWN | visible when `upgradeLevel > 0` / `> 1` | same setter (2nd arg) |
| ↳ second (cooldown) gauge | **does not exist**: `BoostCooldown[3]` + `BoostCooldownUpgradeLevel` are native only, 0 cooldown setters; 1-frame unnamed clip `ch1040` at (5.0, −83.7) | — | — | — | — | seconds in native code only (`BoostCooldown` tier 0 = **12.0 s**) | **none** |
| **Health** | `HudMaster.LeftSideParent.Health` (class `Timeline_390`, 162 frames) | **−479.228, −328.300, 8.318** | 10.0° | **(32.8, 55.7)** — **top-left** | **UNKNOWN** | **proportion 0…1** per bar; `max > 1` selects **5 armour tiers** | `UC_SetHealth(health:Number, max:Number)`, `UC_SetHealthBarVisible(visible, introSuffix)` |
| ↳ health fill | `Health.Healthbar.Bar` | local (MATRIX3D, not decoded) | — | top-left | UNKNOWN | `min(1, health)` | `UC_SetHealth` |
| ↳ armour fill | `Health.ArmourForeground` / `ArmourBackground` | local | — | top-left | UNKNOWN | `max(0, health − 1)`; tier `= int((max − 1) * 4)` → `Armour0…Armour4` | `UC_SetHealth` |
| ↳ damage number | `Health.DamageEffectMovie` | `StageWidth*x`, `StageHeight*y` per call, rotationY ±60 | — | where the hit landed | UNKNOWN | **frames as a string**: `String(frames)` | `UC_SetImpactDamageFlash(part, x, y, frames)` |
| **Ammo** | **no ammo gauge**: weapon *names* + slot states only (see §5) | — | — | — | — | — | `UC_SetPrimaryWeapon(name)`, `UC_SetSecondaryWeapon(name, b, b)`, `UC_SetSpecialWeapons(3 × int)`, `UC_SetWeaponFeedback(b, b)` |
| ↳ cannon cooldown | heavy reticle `recticuleHeavy` states `Ready` / `PreReady` / `PreReadyLevel1/2` / `Blank` | — | — | reticle (centre) | UNKNOWN | **5 categorical states, 0…4** | `UC_SetCannonCoolDown(int)` |
| ↳ Vulcan heat | **not drawn**: `HeatBarStart`, `HeatBarSize` are 2 of the 6 script fields on `Batmobile_Cannon_V2`; **0 of 252** setters mention heat | — | — | — | — | (unknown scale, no setter) | **none** |
| ↳ energy charges | energy system labels `Charges2/3/4`, `Full`, `BecomeFull`, `Use`, `LoseToHit`, `LoseToInaccuracy`, `Empty` | — | — | — | UNKNOWN | **charges: int count + max**, plus `proportion` 0…1 | `UC_SetEnergySystemParams(charges, max, proportion, instant, state)` |
| **Selector (mode)** | `BattleAndZoomInterface` (+ `ZoomInterfaceTopBottom`, `battle_mode_topCorner`/`bottomCorner`, `battleMode_crosses_group_anim`) — **invisible in `DRIVE`** | — | — | — | UNKNOWN | **enum: DRIVE / BATTLE / ZOOMED**; opacity 0…1 | `UC_SetBattleAndZoomMode(battle:Boolean, zoomed:Boolean)`, `UC_SetBattleModeOpacity(Number)`, `UC_SetSelectiveVisibilityModule(name)` |
| other: combo | `HudMaster.LeftSideParent.Combo` | −460.237, −263.250, 36.326 | 26.0° | (51.8, 120.8) | UNKNOWN | proportion 0…1 + count + seconds | `UC_SetBatmobileCombo(proportion, count, seconds)` |
| other: XP | `Health.XPbar` | local | — | inside the health clip | UNKNOWN | proportion 0…1 | `UC_SetXpLevel(proportion, instant)` |
| other: clock | `HudMaster.RightSideParent.ClockTimer` | 399.200, 60.750, 0.000 | −38.0° | right group | UNKNOWN | time, states `Initial/Pause/Resume/Expired/ExpiredOutro` | no `UC_*` setter in the 37 (timeline-driven) |
| other: winch | `WinchMovie` inside `RemoteInterface` | RemoteInterface at −525.275, 225.000, 51.171, yaw 26° | 26.0° | (−13.3, 609.0) | UNKNOWN | **cone angle, needle angle, onTarget** (degrees + bool) | `UC_SetWinchMeter(coneAngle, needleAngle, onTarget)`, `UC_SetWinchMeterVisible(b)` |

**Colour is UNKNOWN on every row.** No decoded record in `HUD.md`, `HUD_SPEC.json`,
`HUD_INTERFACES.json`, `Working/HUD/CLUSTER.json` or `G3-HUD-CLUSTER.md` carries a gauge colour or a
hex value; the only colour-shaped member is `UC_SetColorTransform(param1…param6)` on
`HudModuleBatmobile` and `HudModuleTargets` (**decoded signature, undecoded use**). Where colour would
be settled: the decompiled `HudModuleBatmobile` AS3 colour constants, the GFx tag stream's
`DefineShape` fills, and the `HudModuleBatmobile.Image_I1*.tfc` atlases (`_BmAK_grab/hud/modules/…`,
outside the repo). It is not in this repo, so it is not claimed.

---

## 3. Boost — the one gauge that is always on while driving (decoded)

| item | value | source |
|---|---|---|
| setter | `UC_SetBoostLevel(level:int, upgradeLevel:int)` | `HUD_INTERFACES.json` → `HudModuleBatmobile.setters` |
| range | **0…100** (percent), `upgradeLevel` **0…2** | `HUD.md` §4 |
| fill | `this.FillMovie.gotoAndStop(this.BoostLevel + 1)`; clip **102 frames**; scale-y **0.011 → 1.0**, fixed anchor, `Cap` rides y **9.5 → −182.5** | `Working/HUD/CLUSTER.md` §2 |
| visibility | shown while `level < 100`; `UC_HideBoostGauge()` when `level >= 100` unless `bHoldBoostOnscreenUntilUsed` | same |
| motion cues | `Charging` on `Background.Upgrade1/2`; `Decrease` on `Cap` + `Shake` on the bar while draining | same |
| native values it mirrors | `RVehicleSimBatmobile.BoostDuration` **2.0 s** (offset 664), `BoostCooldown` tier 0 **12.0 s** (668), `CurrentBoostTimer` 1.0 (808), `BoostCooldownUpgradeLevel` (680) | `CLUSTER.json → native.sim_defaults` |
| units | the gauge shows **percent of boost available**, not seconds; the 2.0 s / 12.0 s timings exist only in native code and never reach the movie | derived from the setter + native table |

So the BmAK bar is a **fuel/charge bar with 101 steps**, vertical and bottom-anchored, with two
badge clips for the recharge-upgrade tier.

---

## 4. Health — proportion plus armour tiers, drawn top-left (decoded)

`UC_SetHealth(health, max)`; every expression below is extracted into
`HUD_SPEC.json → bmak.health_contract` and re-checked by `hud_spec.py --check`:

| term | expression | reads as |
|---|---|---|
| `health` | `this.TargetHealthProportion = param1` | a **proportion**: 1.0 = one full bar, **not hit points** |
| `max` | `this.HealthMax = param2` | the bar ceiling; **above 1 it adds armour tiers** |
| bar fill | `Math.min(1, this.CurrentHealthProportion)` | first bar always 0…1 |
| armour fill | `Math.max(0, this.CurrentHealthProportion - 1)` | everything above 1 is armour |
| armour tier | `param2 > 1 ? int((param2 - 1) * 4) : 0` | selects `Armour0…Armour4` (5 labels) |
| pulse | `param1 < 0.2 && TargetHealthProportion < 0.2` | pulses below **20 %** |
| sweep | `MaxHealthChangePerFrame = 0.05` at 30 Hz | **0.667 s** empty → full |
| offscreen | `GoOffscreenTimer = 2` | hides **2 s** after full and XP settled |
| visibility | `UC_SetHealthBarVisible`, battle forces it with `Delayed` | damage shows it; battle intro is delayed |

Position: `Health` at **(−479.228, −328.300, 8.318)**, yaw 10°, screen **(32.8, 55.7)** — the
operator's "top left in battle mode" lead is confirmed by the decoded transform, and the bar is the
same place in drive; only its visibility differs.

Native side: `RVehicle.MaxHealth` (IntProperty, offset **2148**) exists; **no armour field was found**
in the BmSDK headers (`CLUSTER.md` UNKNOWN), even though the movie draws five armour tiers from
`max`'s value.

---

## 5. Ammo — what the cluster actually shows, and what it does not (decoded)

The 37 Batmobile setters contain **no ammo, magazine, bullet or heat member**. What exists:

| member | args | what it drives |
|---|---|---|
| `UC_SetPrimaryWeapon(name:String)` | name only | the primary slot label |
| `UC_SetSecondaryWeapon(name:String, b:Boolean, b:Boolean)` | name + 2 flags | secondary label and its two states |
| `UC_SetSpecialWeapons(int, int, int)` | **3 × state** | `Unavailable` / `Available` / `Used` / `Lost` |
| `UC_SetCannonCoolDown(int)` | **0…4** | reticle `Ready` / `PreReady` / `PreReadyLevel1` / `PreReadyLevel2` / `Blank` |
| `UC_SetMachineGunAccuracyFrame(int)` | frame index | MG accuracy/reticle frame |
| `UC_SetWeaponFeedback(Boolean, Boolean)` | 2 flags | hit/feedback flashes |

Heat: `Batmobile_Cannon_V2` carries **6 script fields**, `HeatBarStart` and `HeatBarSize` among them
(`MECHANICS.md` rows for all four packages); **0 of 252** `UC_*` setters across 19 movies mention
heat (`JC3_HUD_WEAPONS.md` §7). The Vulcan's heat bar is therefore **an absence on both sides**.

Energy (the other "ammo-like" gauge): `UC_SetEnergySystemParams(charges:int, max:int,
proportion:Number, instant:Boolean, state:int)` with the 2/3/4-charge and
`Use`/`LoseToHit`/`LoseToInaccuracy`/`Empty` labels. It is a **charge count + 0…1 proportion**, not a
round count.

---

## 6. Selector — the mode machine, and why it is not a driving gauge (decoded)

`UC_SetBattleAndZoomMode(battle, zoomed)` drives `ModuleStruct_Batmobile.SetBattleAndZoomMode`,
which:

```
DRIVE  --battle------------> BATTLE
DRIVE  --zoomed------------> ZOOMED (implies battle)
BATTLE --zoomed------------> ZOOMED
BATTLE --battle off--------> DRIVE
ZOOMED --zoomed off--------> BATTLE
ZOOMED --battle off--------> DRIVE
```

and sets `BattleAndZoomInterface.visible` **false in `DRIVE`**. So while driving there is no visible
mode selector; the interface (with `ZoomInterfaceTopBottom`, `battle_mode_topCorner`,
`bottomCorner`, `battleMode_crosses_group_anim`) arrives on the `DRIVETOBATTLE` transition.
`UC_SetBattleModeOpacity(0…1)` dims the overlay rather than switching screens;
`UC_SetSelectiveVisibilityModule(name)` adds/removes whole module groups and is the container's
per-mode visibility hook.

---

## 7. JC3 element and setter, per gauge (decoded)

JC3's `ui/hud.gfx` (260 AS3 scripts, 1280×720, 30 fps) exposes this vehicle API
(`HUD_SPEC.json → jc3.vehicle_api`, `HUD.md` §6):

| BmAK gauge | JC3 element | JC3 setter (signature) | what the JC3 element reads | what we feed so the number equals BmAK's |
|---|---|---|---|---|
| **Speed — BmAK has none** | `MCI_speedo` (inside `MCI_safe_area_bottom_left`, with `MCI_vehicle`); `MCI_speedometer` also touched by the secondary meter | `InitPrimaryMeter(type:int, big_tick:Number, max_value:Number)`, `SetPrimaryMeterValue(value:Number)`, `SetVehicleType(type:int)`, `SetVehicleInfo(name:String)` | a **speed magnitude** scaled onto a 250° dial (`SPEEDO_DEGREES = 250`, smoothing **0.05 s**), units chosen by `SetVehicleType` (`hud_kph` / `hud_knots` label only) | **Hide it, do not feed it.** BmAK draws no speedometer, and `SetVisibilities()` sets `MCI_speedo.visible = true` unconditionally, so suppression needs a **private `ui/hud.gfx` copy** (R7). If a speedo is ever required: feed `|Velocity|` **cm/s → km/h by ×0.036**, with `max_value = 126` (BmAK's `FakeExtraSpeedMax` **3500 cm/s**), and add `FakeExtraSpeed` so the bar tracks boost too. |
| **Boost** | `MCI_nitro_meter` (`InitVehicleNitrous`/`UpdateVehicleNitrous` own it; `HideVehicleUi()` hides it) | `InitVehicleNitrous(recharge:Number)`, `UpdateVehicleNitrous(recharge:Number)`, `HideVehicleNitrous()` | a **recharge fraction 0…1**, 1 = ready (ready sound at 1) | **`recharge = level / 100`.** Both sides treat 1.0 as full/ready, so no inversion. Direction differs (BmAK vertical/bottom-anchored, JC3 horizontal) — C4. The badges have no JC3 member. |
| **Health** | `MCI_vehicle` health paint / bar, implemented under `hud_code/health/*` (`MCI_vehicle` is also touched by `InitPrimaryMeter` and `InitSecondaryMeter`) | **no public vehicle-health function in the 260 scripts' vehicle API** — the caller is native (**UNKNOWN**) | a vehicle health **proportion** painted over the vehicle cluster | feed the BmAK **proportion**, i.e. `min(1, health)`; if BmAK health is hp/maxhp, divide **before** sending. Armour (`health > 1`, 5 tiers) has **no JC3 field** — it clips at full (C2). |
| **Ammo** | `MCI_safe_area_bottom_right.MCI_vehicle_weapons0`, `…weapons1` (2 slots), each with `MCI_bullet_bar`, `MCI_bullet_bar_anim`, `MCI_radial_loader_cooldown`, `MCI_selected_weapon_icon`, `TXT_bullet_ammo`, `TXT_slash_mark`, `TXT_selected_inventory_ammo`, `TXT_name`, `MCI_inventory_infinity` | `InitVehicleWeapons(slot_index, weapon_id, weapon_name, infiniteAmmo=true, magazine_ammo=-1, magazine_size=-1, inventory_ammo=-1, weapon_cooldown=-1, is_overcharged=false)`; `UpdateVehicleWeapons(slot_index, new_magazine_ammo_amount, total_ammo, is_low_ammo, weapon_cooldown=-1, is_overcharged=false)` | **rounds**: `65 * ammo / size` bullet-bar frame, `TXT_bullet_ammo` / `TXT_selected_inventory_ammo` text, infinity icon | JC3 reads **rounds**; BmAK has **no round count**. Feed `infiniteAmmo = true` (hides the counters, shows `MCI_inventory_infinity`) and pass BmAK's weapon names into `weapon_name`. For the 5-state cooldown, feed `weapon_cooldown` as a **fraction where 1 = full ring, −1 = no loader** (derived mapping, §8). |
| **Selector (mode)** | **none** — JC3 has no DRIVE/BATTLE mode element; the only slot-level selector is the 2-slot array index `EVEHICLE_WEAPON_SLOT_MAIN` / `_ALTERNATIVE` | no setter | n/a | nothing to feed. The mode change must be carried by the parts/entity (see `battle-mode-transform-plan.md`), not by the HUD. |
| ↳ reticle | `UpdateWeaponReticle(show, weapons_look, reticle_size, reticle_shape)`; 14 shapes, `E_RETICLE_CANNON = 8` exists but nothing maps it to a vehicle cannon (**shape id UNKNOWN**) | same | shape id + look colour + size | feed `reticle_shape = 8` (cannon), `weapons_look` 0…4 by target state, and drive `show` from BmAK's cooldown state. |
| **Energy charges** | none | none | — | **out**: no charge gauge in JC3. |
| **Vulcan heat** | none — JC3 has **0 heat parameters** in the vehicle-weapon API; the movie's "heat" is the 11-state police wanted level | none | — | **out**, stated absence on both sides. |

---

## 8. Where JC3 reads a different quantity — the four conversions to get right

1. **Boost: percent → recharge fraction.** BmAK `level` is 0…100 **available**; JC3 `recharge` is
   0…1 **toward ready**. `recharge = level / 100` is the identity you want (both full = 1.0). Do not
   invert.
2. **Health: hit points → proportion, and armour dropped.** BmAK's setter already takes a
   proportion (`TargetHealthProportion`), but the *game* side has `RVehicle.MaxHealth = hp`; the
   conversion is `health = hp / maxhp` and then `max = 1` (no armour). Sending raw hp makes a
   1,200 hp car read 1,200 bars, since the movie does `min(1, h)`.
3. **Ammo: rounds → infinity.** BmAK has no rounds; JC3's slot divides `65 * ammo / size`, so
   feeding `ammo = 0` blanks the bar and `ammo = -1` trips the early return. Use
   `infiniteAmmo = true` so the slot shows `MCI_inventory_infinity` and no counter — that is the
   closest truthful rendering of "no ammo gauge in BmAK".
4. **Cooldown: 5 categorical states → 0…1 + −1.** JC3 wants a fraction (`SetCooldownRotation`
   rotates `MCI_mask_0_50` to `min(rot,180)` and `MCI_mask_50_100` to `max(rot−180,0)`, `rot =
   weapon_cooldown * 360`). **Derived proposal:** state 0 (`Ready`) → `−1` (hide the loader, reticle
   `Ready`); states 1…4 → `0.75, 0.5, 0.25, 0.0` so the ring empties as BmAK steps toward `Blank`.
   The pinning of the five labels to five fractions is a mapping, not a decoded BmAK value.

Speed is the fifth and is not a conversion: it is a **suppression** (C3).

---

## 9. Order of work, and the cheapest experiment

1. **Suppress `MCI_speedo` and keep `MCI_nitro_meter` + `MCI_vehicle`** in a private `ui/hud.gfx`
   copy — the only decoded route, because `SetVisibilities()` re-shows the speedo unconditionally and
   `HideVehicleUi()` is the only function that hides it.
2. **Feed boost** with `InitVehicleNitrous(level/100)` from a hook. There is **no caller in the
   movie** (0 call sites for `UpdateVehicleNitrous`; `InitVehicleNitrous`'s caller is native), so the
   hook is the work.
3. **Feed the two weapon slots** with `infiniteAmmo = true` and BmAK's names; `weapon_cooldown` from
   the cooldown state per §8.4. The entity has **no weapon component** yet (`T-HUD5`: "blocked: the
   HUD supports it, the entity does not"), so this waits on the weapon work.
4. **Leave the mode selector alone** — no JC3 element, and BmAK does not show it in `DRIVE` either.

**5-minute experiment (read-only, no game launch):** `HUD_SPEC.json` already proves the two movie
APIs; the open question is only *who calls them*. Dump both movies' `PlaceObject`/`DefineSprite`
trees with `ffdec -dumpSWF` and compare the `MCI_nitro_meter` / `MCI_speedo` child names — if the
JC3 element names match the ones in `hud.as`, the private-copy route in §9.1 is sound and no import
of BmAK art is needed. Importing BmAK's `BoostMovie` sprite into `hud.gfx` stays **UNKNOWN** (no
evidence either way; CLUSTER.md §7).

---

## 10. If files are touched later — change, file, revert

Nothing was modified for this report. When the build starts:

| intended change | file | why it is the right file | revert |
|---|---|---|---|
| hide `MCI_speedo` for this vehicle | a **private copy** of `ui/hud.gfx` (R7), `SetVisibilities()` | that function is the only thing that re-shows the speedo; editing the shared movie is forbidden | delete the private copy; the game's `ui/hud.gfx` is untouched |
| drive nitrous / health paint | the HUD caller (hook), not the movie | both APIs have 0–1 movie call sites; the caller is native | remove the hook |
| weapon slots | `InitVehicleWeapons` caller + the entity's weapon component | the movie is already correct; the entity is what is missing (`T-HUD5`) | remove the component / the call |

## 11. UNKNOWNs, each with its settler

| # | unknown | settler |
|---|---|---|
| U1 | **gauge colours** (all of them) | decompiled `HudModuleBatmobile` AS3 colour constants, GFx `DefineShape` fills, `Image_I1*.tfc` atlases |
| U2 | JC3 vehicle-health setter name | the native HUD binding; the movie has no public function (**0** in the 260-script vehicle API) |
| U3 | which `reticle_shape` a vehicle cannon gets | native; `E_RETICLE_CANNON = 8` exists but nothing maps it |
| U4 | whether BmAK art can be imported into `hud.gfx` | SWF/AVM tag comparison (both are GFx v0f? unproven) |
| U5 | the 5 cooldown states → fractions pinning | BmAK's native cooldown timer; the movie only receives the state int |
| U6 | armour tiers' native source (`max`'s origin) | `RVehicle.MaxHealth` = 2148 exists; no armour field found in the BmSDK headers |

## 12. Sources

`Research/BatmobileGrab/HUD.md` (§4 mode machine and setters, §5 element list, §6 JC3 API, §8 open
questions), `HUD_SPEC.json` (`bmak.uc_setters`, `constants`, `health_contract`; `jc3.vehicle_api`,
`constants`), `HUD_INTERFACES.json` (`HudModuleBatmobile` 37 setters, `HudModuleTargets` 16),
`SPEEDOMETER.md` (no movie speedometer; `bDebugSpeedometer` off in both configs; the native fields),
`MECHANICS.md` (`HeatBarStart`/`HeatBarSize` on `Batmobile_Cannon_V2`);
`Working/HUD/CLUSTER.md` + `Working/HUD/CLUSTER.json` (clip transforms, boost fill, badges, native
defaults, JC3 routes, C1–C5), `tmp/freebuff/reports/G3-HUD-CLUSTER.md` (screen estimates, speedo
suppression route), `tmp/freebuff/reports/HUD_CLUSTER_ELEMENTS.md` (which positions are AS3-decoded);
`Research/JC3Grab/JC3_HUD_WEAPONS.md` (2 slots, 9/6-arg weapon API, cooldown rotation, reticle
shapes, heat absence, lock-on POI), `HUD.md` §6 (`MCI_speedo`, `InitPrimaryMeter`,
`SPEEDO_DEGREES = 250`, `SPEEDO_SMOOTHING_TIME = 0.05`).
