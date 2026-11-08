# Weapon switching — how BmAK selects cannon / Vulcan / missiles / EMP / hacker / sonar, and what JC3 input can carry

**Question:** describe exactly how a BmAK player cycles between cannon, Vulcan, missiles, EMP,
hacker and sonar (buttons, timing, on-screen feedback); then trace JC3's vehicle weapon switch
(input action names, slot order) and give the mapping that puts the same buttons on the same weapon
in the same order.

**Verdict, in one paragraph.** BmAK does not cycle — it **direct-selects four weapon classes by
index**: `B` → class **1**, `X` → **2**, `Y` → **3**, **D-Pad Up** → **4**
(`SelectVehicleWeapon 1/2/3/4`, decoded from the bytecode arguments, `DefaultInput.ini:259/268/
269/270`). Each press **also attempts to fire** (`TryToFireWeapon` twice behind `ReadyToFire`), and
release calls `ReleaseVehicleWeapon`; there is **no decoded timer** for the switch and no decoded
press-vs-hold rule. Feedback is a per-frame `DrawWeaponSelectHud` plus `DrawWeaponPowerLevel` in
`DrivingMode`, backed by the movie's `UC_SetPrimaryWeapon` / `UC_SetSecondaryWeapon` /
`UC_SetSpecialWeapons` / `UC_SetWeaponFeedback` and the 5-state cannon-cooldown reticle. On the JC3
side there is **no vehicle weapon-switch action at all** — the 16 land-vehicle actions include only
`FIRE_VEHICLE_WEAPON_PRIMARY` (RB / MOUSE1) and `FIRE_VEHICLE_WEAPON_SECONDARY` (LB / MOUSE2);
`NEXT_WEAPON` / `PREV_WEAPON` exist but are **on-foot** (mouse wheel), and `DP_UP/DOWN/LEFT/RIGHT`
have **UNKNOWN** owners. The HUD holds exactly **2 slots** — index 0 `EVEHICLE_WEAPON_SLOT_MAIN`,
index 1 `EVEHICLE_WEAPON_SLOT_ALTERNATIVE` — so the mapping is: classes 1/2 → the two fire slots,
class 4 → `USE_ITEM` (which is already on **RPADUP**, the same D-Pad Up BmAK uses), class 3 →
`USE_VEHICLE_MOD`. "Same button" cannot be completed for B/X/Y because JC3 binds **no face button to
any vehicle action**; that last step is a `settings/keymap_gamepad.bin` rebind, and whether a
dropzone-supplied keymap is honoured is **UNKNOWN**.

Labels: **decoded** = read from the cited file at the cited export/line; **derived** = arithmetic or
mapping over decoded inputs; **UNKNOWN** = searched and absent, with where it would be settled.

---

## 1. The BmAK control set that reaches weapon selection (decoded)

`Research/BatmobileGrab/CONTROLS.md` §Action table, `BINDINGS_MERGED.md` (the 366-entry oracle),
`DRIVINGMODE.md` §1 and §2 (token-by-token function bodies).

| button (pad) | ini line | commands fired | argument | decoded? |
|---|---|---|---:|---|
| **B** | `DefaultInput.ini:268` | `QuickGadgetB` … `ReleaseQuickGadgetB` | **1** | decoded (`EX_IntOne`, offsets 5–6) |
| **X** | `DefaultInput.ini:269` | `QuickGadgetX` … `ReleaseQuickGadgetY` | **2** | decoded (`EX_IntConstByte` = 2, offset 5) |
| **Y** | `DefaultInput.ini:270` | `QuickGadgetY` … `ReleaseQuickGadgetY` | **3** | decoded (`EX_IntConstByte` = 3, offset 5) |
| **D-Pad Up** | `DefaultInput.ini:259` | `SelectVehicleWeapon 4` \| `OnRelease ReleaseVehicleWeapon 4` | **4** | decoded (literal in the binding line) |
| **RT** | `DefaultInput.ini:252` | `BatmobileFireButton`, `Button bFireVehicleWeapon` | — | fire, not select |
| **RB** | `DefaultInput.ini:272` | `SecondaryFireVehicleWeapon`, `bFireVehicleSecondaryWeapon`, `PursuitModeTagGun`, `ToggleDrivingCamera` | — | fire, not select |
| **D-Pad Left / Right / Down** | `:257` / `:258` / `:260` | challenge wheel, most-wanted menu, gadget-select wheel | — | **no weapon token** |

Two handlers are wrappers, three are stubs:

| command | body | script bytes | what it does |
|---|---|---:|---|
| `DrivingMode.QuickGadgetB` | export 105042 | **9** | `VCALL SelectVehicleWeapon(1, <0x4a>)` |
| `DrivingMode.QuickGadgetX` | export 105040 | **10** | `VCALL SelectVehicleWeapon(2, <0x4a>)` |
| `DrivingMode.QuickGadgetY` | export 105044 | **10** | `VCALL SelectVehicleWeapon(3, <0x4a>)` |
| `DrivingMode.ReleaseQuickGadgetB` | 105043 | 9 | `ReleaseVehicleWeapon(1, …)` |
| `DrivingMode.ReleaseQuickGadgetX` | 105041 | 10 | `ReleaseVehicleWeapon(2, …)` — **not bound in the ini chain** |
| `DrivingMode.ReleaseQuickGadgetY` | 105045 | 10 | `ReleaseVehicleWeapon(3, …)` |
| `DrivingMode.SelectVehicleWeapon` | 104971 | **448** | the real selector (see §1.1) |
| `DrivingMode.ReleaseVehicleWeapon` | 104975 | 130 | the release counterpart |

**So the six weapons are reached through four indices, not a carousel.** There is no
"next/previous weapon" command anywhere in the BmAK pad scheme, and no weapon is reached by pressing
the same button again.

### 1.1 What `SelectVehicleWeapon` actually does (decoded body, 448 script bytes)

| call | target | meaning |
|---|---|---|
| `Core.IsButtonInputIgnored()` | gate | ignore the press while input is suppressed |
| `ReadyToFire()` → `RVehicleWeapon.TryToFireWeapon()` | fire path 1 | **the select press fires** if the weapon is ready |
| `IsFiring()` → `ReadyToFire()` → `RVehicleWeapon.TryToFireWeapon()` | fire path 2 | second attempt (the two paths are state-machine branches, not two weapons — the branches themselves are not resolved) |
| `RVehicleBatmobileBase.TryRightingFlip(false, …)` | utility | righting flip attempt |
| `Core.TriggerEventClass(RSeqEvent_BatmobileRiddlerButton, self, 0, 74)` | script event | fires the Riddler-button sequence event (a puzzle hook, not a weapon) |

`RVehicleWeapon.TryToFireWeapon` (109 script bytes) itself calls `FireWeapon()` and
`BattleModeExitted()`. **This is the single most important BmAK fact for the port:** the slot keys
are not "select-only" — pressing B/X/Y/D-Pad Up **selects and tries to fire in the same press**.
That is why the control reads as a quick-gadget, not a weapon wheel.

### 1.2 Mode dependence (decoded)

* `BattleMode.BeginState`: `EquipWeaponAchetype(BattleModePrimaryWeapon)` **and**
  `EquipSecondaryWeapon(SecondaryWeapon)`.
* `PursuitMode.BeginState`: `EquipWeaponAchetype(PursuitModePrimaryWeapon)` only.
* The mode's primary resolves to a class name: `PursuitModePrimaryWeapon` → `Weapons.Batmobile_Booster`
  (`RBatmobileBooster`), `BattleModePrimaryWeapon` → `Weapons.Batmobile_Heavy_Cannon_Primary`
  (`RBatmobileHeavyCannon`) — `COLLISION_WHERE.md` rows 5236 / 5244 (decoded name indices).
* **UNKNOWN:** which object sits behind each of `SelectVehicleWeapon`'s indices 1…4. The literals
  are decoded; the class table is not (`DRIVINGMODE.md` §"UNKNOWN", `CONTROLS_CONSUMERS.md` §3).

---

## 2. The six weapons and the slots they can occupy

The six classes exist in the packages (`WEAPONS.md`, `MECHANICS.md`):

| weapon | entity class | evidence |
|---|---|---|
| cannon (heavy) | `RBatmobileHeavyCannon` | `WEAPONS.md` §2/§4; `Batmobile_Heavy_Cannon_Primary` |
| Vulcan / chain gun | `RBatmobileCannon` (fields `HeatBarStart`, `HeatBarSize`) | `MECHANICS.md` rows for all four packages |
| missiles | `RBatmobileMissileLauncher` (`LockOnSound`, `TargetSwitchName`) | `WEAPONS.md` §5 |
| EMP | `RBatmobileEMPMissile` **and** `RBatmobileEMP` (burst) | `MECHANICS.md` rows 1459 / 1458 |
| hacker | `RBatmobileAllegianceSwitcher` (`Drone_Hacker`) | `WEAPONS.md` §6 |
| sonar | `RBatmobileSonar` (`ChargingScreenShake`, `BlastScreenShake`) | `MECHANICS.md` row 1465 |
| (also) booster, winch | `RBatmobileBooster`, `RBatmobileWinch` | `COLLISION_WHERE.md` 5236; `WEAPONS.md` |

The HUD exposes **five slots**, not six: `UC_SetPrimaryWeapon(name)` (1),
`UC_SetSecondaryWeapon(name, b, b)` (1) and `UC_SetSpecialWeapons(int, int, int)` (**3**), each
special running `Unavailable` / `Available` / `Used` / `Lost` (`HUD.md` §4). The energy system adds
a separate charge gauge (`Charges2/3/4`, `Full`, `BecomeFull`, `Use`, `LoseToHit`,
`LoseToInaccuracy`, `Empty`).

**Derived, and flagged as such:** the only distribution consistent with the decoded counts is
primary + secondary = the two mode primaries (booster / heavy cannon), and the three special slots =
three of {Vulcan, missiles, EMP, hacker, sonar}. Which three is **not decoded** — the class-index
table is the gap, not the slot model.

---

## 3. Timing (what is decoded, and what is not)

| quantity | value | status |
|---|---|---|
| select → fire | same press (`TryToFireWeapon` inside `SelectVehicleWeapon`) | decoded |
| release | `ReleaseVehicleWeapon` on the button's `OnRelease`, same index | decoded |
| hold vs press threshold | — | **UNKNOWN**: `hold_vs_press_timings` = "UNKNOWN (no timer constants resolved for B/LT; DualPlayPressed uses 0.001)" |
| select cooldown / swap lockout | — | **UNKNOWN**: no timer constant in `SelectVehicleWeapon`'s 448 bytes; the only nearby duration is `PreventModeSwitchDuration` (0x9716) which gates **mode** switching, not weapons |
| cannon cooldown feedback | 5 states 0…4, driven by `UC_SetCannonCoolDown(int)` | decoded |
| Vulcan heat | `HeatBarStart` / `HeatBarSize` on the weapon entity; **0 of 252** HUD setters carry heat | decoded absence |
| weapon fire cadence | per-weapon (`ChainGunSpin` 3.9 s clip, `Cannon_Fire` 0.7 s) — not part of selection | decoded in `ANIMATIONS.md` |

So the honest timing answer: **press-to-select is instantaneous and also fires; release ends it;
no switch animation, delay or cooldown is decoded.**

---

## 4. On-screen feedback (decoded)

| layer | element / function | what it shows |
|---|---|---|
| per-frame draw | `DrivingMode.DrawWeaponSelectHud` (export 104963, **415** script bytes) | the weapon-select readout, drawn from the driving state each frame |
| per-frame draw | `DrivingMode.DrawWeaponPowerLevel` (export 104955, **272** bytes) | the weapon power/charge level |
| per-frame draw | `DrivingMode.DrawSuperEjectBar` (export 104958, 354 bytes) | super-eject charge (adjacent, not a weapon) |
| movie: slot names | `UC_SetPrimaryWeapon(String)`, `UC_SetSecondaryWeapon(String, Boolean, Boolean)` | the two named slots |
| movie: specials | `UC_SetSpecialWeapons(3 × int)` → `Unavailable` / `Available` / `Used` / `Lost` | three special-weapon icons/states |
| movie: feedback | `UC_SetWeaponFeedback(Boolean, Boolean)`, `UC_SetMachineGunAccuracyFrame(int)` | hit/feedback flashes, MG reticle frame |
| targets module | `UC_SetBatmobileWeapon(name, Boolean)`, `UC_SetBatmobileWeaponHit(Boolean)`, `UC_SetBatmobileWeaponFailure(Boolean, Boolean)` | target box reacts to **weapon events**, not to a selected index |
| reticle | `UC_SetCannonCoolDown(0…4)` → `Ready` / `PreReady` / `PreReadyLevel1` / `PreReadyLevel2` / `Blank` | cooldown ring/state |
| audio | `RVehicleWeapon.LockOnBeepSound` / `LockedOnSound` / `ReloadSound`, `RBatmobileCannon.ChainGunCooledSound` / `ChainGunOverheatSound`, `RBatmobileSonar.ScannerOnSound` | per-weapon cues; **no decoded "weapon selected" sound** |

There is **no decoded selection animation and no selection sound**: the visible change is the slot
label/icon and the reticle state. The heavy reticle itself lives in the battle overlay
(`recticuleHeavy`), which is why the weapon readout is much more visible in BATTLE than in DRIVE.

---

## 5. JC3's vehicle input (decoded) — there is no switch action

`Research/JC3Grab/INPUT.md` (the decoded action table from `settings/keymap_gamepad.bin` +
`keymap_keyboard.bin`, 474 bindings; action ids are the Jenkins hash of the name for 448 of them).

The **complete** land-vehicle action set is 16 names:

```
ACCELERATE, CHALLENGE_RESET_VEHICLE, ENTER_VEHICLE, EXIT_VEHICLE,
FIRE_VEHICLE_WEAPON_PRIMARY, FIRE_VEHICLE_WEAPON_SECONDARY, HANDBRAKE,
PRECISION_AIM, REVERSE, SOUND_HORN_SIREN, TURN_LEFT, TURN_RIGHT,
USE_ITEM, USE_VEHICLE_MOD, VEHICLE_CAM, VEHICLE_RELEASE_GRAPPLE
```

| action | gamepad | keyboard | role |
|---|---|---|---|
| `FIRE_VEHICLE_WEAPON_PRIMARY` | **RSHOULDER** | MOUSE1 | slot 0 fire |
| `FIRE_VEHICLE_WEAPON_SECONDARY` | **LSHOULDER** | MOUSE2 | slot 1 fire |
| `USE_ITEM` | **RPADUP** | E | the only D-Pad Up vehicle action |
| `USE_VEHICLE_MOD` | RPADRIGHT | MOUSE3 | "vehicle mod" — overcharge/ability |
| `PRECISION_AIM` | RSTICKBUTTON | MOUSE3 | aim |
| `VEHICLE_CAM` | RSTICKBUTTON | B | camera |
| `ENTER_VEHICLE` / `EXIT_VEHICLE` | **both RPADUP** | E | shared enter/exit |
| `NEXT_WEAPON` / `PREV_WEAPON` | — | **MWHEELUP / MWHEELDOWN** | **on-foot only** |
| `DP_UP` / `DP_DOWN` / `DP_LEFT` / `DP_RIGHT` | LPADUP / DOWN / LEFT / RIGHT | — | **UNKNOWN** mode owner |

`INPUT.md`'s own verdict table says it plainly: *"vehicle weapon selection … actions matching
`NEXT_WEAPON|PREV_WEAPON|SELECT.*WEAPON|WEAPON.*SELECT` → `['NEXT_WEAPON','PREV_WEAPON']` →
**UNKNOWN**"*, and its UNKNOWN list adds *"whether `NEXT_WEAPON`/`PREV_WEAPON` reach a vehicle — both
names exist (keyboard) but no file says which mode consumes them, and G2-11 found 2 driver weapon
slots with no switch action."*

**Slot order (decoded).** `Research/JC3Grab/JC3_HUD_WEAPONS.md` §3: the HUD builds
`new Array(MCI_vehicle_weapons0, MCI_vehicle_weapons1)` — **index 0 = `EVEHICLE_WEAPON_SLOT_MAIN`,
index 1 = `EVEHICLE_WEAPON_SLOT_ALTERNATIVE`**. The entity side names the same two slots
`main_weapon` (hash `851CAABE`) and `secondary` (`00568A74`), with two further slots shipped null.
The movie's setters are `InitVehicleWeapons(slot_index, weapon_id, weapon_name, infiniteAmmo,
magazine_ammo, magazine_size, inventory_ammo, weapon_cooldown, is_overcharged)` (9 args) and
`UpdateVehicleWeapons(slot_index, new_magazine_ammo_amount, total_ammo, is_low_ammo,
weapon_cooldown, is_overcharged)` (6 args); `weapon_cooldown` is 0…1 (`-1` hides the loader) and
`SetCooldownRotation` maps it to `rot = cooldown * 360` across `MCI_mask_0_50` / `MCI_mask_50_100`.

So JC3 has **two addressable weapon slots, two fire buttons, no selector**.

---

## 6. The mapping — same buttons, same weapon, same order

BmAK's model is `4 indices × 1 press-and-fire`, JC3's is `2 slots × 1 fire button + 2 extra actions`.
The closest one-to-one, keeping index order 1→4, is:

| BmAK | index | JC3 carrier | JC3 button (as shipped) | does the button match? |
|---|---:|---|---|---|
| **B** → quick weapon 1 | 1 | **slot 0** `main_weapon` / `MCI_vehicle_weapons0`, fired by `FIRE_VEHICLE_WEAPON_PRIMARY` | RSHOULDER | **no** (face button vs shoulder) |
| **X** → quick weapon 2 | 2 | **slot 1** `secondary` / `MCI_vehicle_weapons1`, fired by `FIRE_VEHICLE_WEAPON_SECONDARY` | LSHOULDER | **no** |
| **Y** → quick weapon 3 | 3 | `USE_VEHICLE_MOD` | RPADRIGHT | **no** |
| **D-Pad Up** → weapon 4 | 4 | `USE_ITEM` | **RPADUP** | **yes** — the one exact match |
| RT fire | — | `FIRE_VEHICLE_WEAPON_PRIMARY` (already slot 0's fire) | RSHOULDER | button differs, role maps |
| RB secondary fire | — | `FIRE_VEHICLE_WEAPON_SECONDARY` | LSHOULDER | button differs, role maps |

**Order is preserved by slot index**, not by button: index 1 → slot 0, 2 → slot 1, 3 → mod, 4 →
item. That is the only ordering JC3 can express, because the two HUD slots are the only addressable
weapon containers and `InitVehicleWeapons` takes `slot_index` as its first argument.

**What cannot be finished in data:**
1. **The face buttons.** JC3 binds **no** face button (A/B/X/Y) to any of the 16 land-vehicle
   actions; the BmAK scheme's three quick-gadget keys have no JC3 vehicle action at all. Reaching
   them means rebinding `settings/keymap_gamepad.bin` — and *"no vehicle entity names an input
   action and none names the keymap: the binding table is global, not per entity"* (0/232 entities
   contain `keymap`). Whether a keymap from a dropzone is honoured is **UNKNOWN** (needs a runtime
   test).
2. **A cycle.** JC3 has no next/previous-vehicle-weapon action, so a cycle (if we want one to match
   the "four quick slots" feel) must be implemented by re-calling `InitVehicleWeapons` on the two
   slots from a graph/native caller — the movie's `UpdateVehicleWeapons` has **0 call sites** in the
   movie and `InitVehicleWeapons` only 2 (both in `TestConstructor`), so the caller is native.
3. **Six weapons into five slots.** BmAK has six weapon classes and four indices; JC3 has two slots
   plus two mod/item actions. At most four weapons can be *selected*; the other two have to be
   states of a slot (as BmAK itself does — `UC_SetSpecialWeapons` draws `Unavailable` / `Available`
   / `Used` / `Lost`, not six icons).

**Recommended build:** keep JC3's two fire buttons as the two mode primaries (booster / heavy
cannon, matching `PursuitModePrimaryWeapon` / `BattleModePrimaryWeapon`), put the three specials on
`USE_VEHICLE_MOD` + `USE_ITEM` + one hot-swapped slot, and rebind D-Pad Up → `USE_ITEM` so the one
button BmAK already uses for a weapon stays a weapon button. Then the only new input is the
quick-gadget pair on B/X/Y, which needs the keymap edit or a native hook.

---

## 7. The cheapest experiment (before any build)

Offline, read-only, no game launch:
1. `INPUT.md` already proves the action set; the open half is **which mode owns `DP_UP`…`DP_RIGHT`**
   and whether `USE_ITEM` is consumed on a land vehicle. Read the two `settings/keymap_*.bin` files
   for the `DP_UP` id and check whether its hash equals `USE_ITEM`'s (`195` in the action table) —
   if `DP_UP` and `USE_ITEM` are the same id, the D-Pad Up mapping is already exact and needs no
   rebind.
2. Then the six-weapon distribution question: read the two `main_weapon` / `secondary` hashes on the
   built private entity and see which two classes they point at; that fixes indices 1 and 2 without
   any native work.

If step 1 shows the ids differ, the keymap rebind is the first build action and its acceptance is a
pilot check (press D-Pad Up in-car and watch the slot icon change).

---

## 8. If files are touched later — change, file, revert

Nothing was modified for this report. The build steps and their revert:

| intended change | file | why it is the right file | revert |
|---|---|---|---|
| rebind face buttons / D-Pad to weapon actions | `settings/keymap_gamepad.bin` (**private copy**, never the archive entry) | the only button→action table; entities cannot name it (0/232) | delete the private copy; the game's own keymap is untouched |
| set slot 0 / slot 1 weapon classes | the private `.ee`'s weapon components (`main_weapon`, `secondary`) | those two hashes are the entity-side slot names | rebuild from the build manifest |
| drive the slot labels/icons | `InitVehicleWeapons` caller (hook), not the movie | the movie's only call sites are `TestConstructor`; the real caller is native | remove the hook |
| show selection feedback | `MCI_vehicle_weapons0/1` (already in `ui/hud.gfx`) | two slots already exist and take a name, id and ammo state | no change needed |

## 9. UNKNOWNs, each with its settler

| # | unknown | settler |
|---|---|---|
| U1 | which weapon class each of `SelectVehicleWeapon(1…4)` selects | the `*PrimaryWeapon` / `SecondaryWeapon` object refs and the class table (not resolved in `DRIVINGMODE.md`); the `EquipWeaponAchetype` arguments in `BattleMode.BeginState` |
| U2 | press vs hold threshold on B/X/Y | no timer constants in the handlers; a runtime read of `LastTriggerAmount`-style state, or the native input path |
| U3 | whether `DP_UP` and `USE_ITEM` share an action id | compare the two hashes in `settings/keymap_*.bin` (§7 step 1) |
| U4 | whether `NEXT_WEAPON` / `PREV_WEAPON` reach a vehicle | the native input→mode consumer; no file names it |
| U5 | whether a dropzone `settings/keymap_gamepad.bin` is honoured | runtime test (none has been run) |
| U6 | which three of the five specials occupy the three special slots | the private entity's weapon component list |
| U7 | whether `SelectVehicleWeapon` fires or only selects on a real press | the branches are unresolved in the 448-byte body; `TryToFireWeapon` is called, but under which branch is not decoded |

## 10. Sources

`Research/BatmobileGrab/CONTROLS.md` (action table: `SelectVehicleWeapon`, `QuickGadget*`,
`ReleaseQuickGadget*`, fire tokens), `BINDINGS_MERGED.md` (lines 97–114: the D-Pad and face-button
command lists), `BINDINGS_KEYBOARD.md` (gamepad rows, `SelectVehicleWeapon 4`),
`CONTROLS_CONSUMERS.md` (§2/§3 the B verdict and the `1/2/3` arguments; §"Precise details"),
`DRIVINGMODE.md` (§1 command→body table with sizes; §2 the `SelectVehicleWeapon` body and the
`QuickGadget*` wrapper bodies; UNKNOWN on the class indices), `DRIVE_MODES.md` (BeginState equips,
`PowerSlide` note), `COLLISION_WHERE.md` (5236/5244 primary-weapon objects), `WEAPONS.md`
(`RBatmobileHeavyCannon`, `RBatmobileAllegianceSwitcher`, `RBatmobileMissileLauncher`),
`MECHANICS.md` (`RBatmobileCannon` heat fields, EMP/sonar entities), `HUD.md` §4 (the five HUD
weapon slots and their setters);
`Research/JC3Grab/INPUT.md` (the 16 land-vehicle actions, their pad/keyboard bindings, the
`NEXT_WEAPON`/`PREV_WEAPON` on-foot-only finding, the "vehicle weapon selection UNKNOWN" verdict,
and the "binding table is global" limit), `JC3_HUD_WEAPONS.md` (§1/§2 the 9- and 6-argument weapon
API, §3 the 2-slot array and `EVEHICLE_WEAPON_SLOT_MAIN/ALTERNATIVE`, §7 the element table);
`tmp/freebuff/reports/entry-exit-and-controls-plan.md` §0.7 (the `main_weapon` / `secondary` hashes
and the 4-index model). The three per-frame draw functions' exports and sizes
(`DrawWeaponPowerLevel` 104955/272, `DrawSuperEjectBar` 104958/354, `DrawWeaponSelectHud`
104963/415) are from `CONTROLS_CONSUMERS.md` lines 96–98.
