# Control scheme — the closest JC3 input system per Batmobile binding, and what the build adds

Card: the BmAK control report (`tmp/freebuff/reports/bmak-control-scheme-storage.md`) and the
control-priority memory (enter `Y`, exit `LB`; inside the car BmAK wins, JC3 keeps pause and
commlink — `Research/BatmobileGrab/CONTROLS_MENU_SCREENS.md` operator block, `GRAB_BACKLOG.md`
D-11). Project rule applied: **a gap is closed by the build, not reported** (`STAGES.md`).

Labels: **decoded** = read bytes/lines at the path named; **derived** = arithmetic or rule shown;
**UNKNOWN** = searched, not found, and the file that settles it named. Memory-only bindings are
labelled as such — they are not evidence of a file.

This is a plan: **no keymap, `.epe`, module, `.stringlookup`, receipt or ledger row was changed**,
no game was launched, no build tree was written. The only file written is this one. Revert = delete
this file.

---

## 0. Answer in eight lines

1. JC3 has **three** input systems, not one: the **global action map**
   (`settings/keymap_gamepad.bin` / `keymap_keyboard.bin`, patch layer: 145 + 104 bindings), the
   **weapon/gadget slot model** (four root object pointers, two fire actions, a 2-slot HUD), and
   **UI prompts** (per-entity `.stringlookup` + a `prompt` member on each interaction entry).
2. The shipped gamepad table has **0 face-button rows** (no A/B/X/Y at all). Every BmAK face button
   is therefore an **addition**, not a displacement; the only BmAK button that collides with a JC3
   token is `LB` (`LSHOULDER`, 8 tokens including `FIRE_VEHICLE_WEAPON_SECONDARY`).
3. The one structural edit the memory rule needs: **`EXIT_VEHICLE` moves off `RPADUP` onto
   `LSHOULDER`**, and `LSHOULDER` loses secondary fire (which moves to BmAK's `RB`). Enter and boost
   can both sit on `Y` — multi-token keys are the shipped shape (`X` and `LSHOULDER` each carry 8).
4. Slot **selection** is the only genuinely absent data member: JC3 has no active-slot index, no
   next/previous action and no weapon group in any `.epe` (`WEAPON_WIRING.md` §2b). The build ships
   the slots (8 across 4 `CCar` roots, `T-WP13`) and the four engine-named actions; which slot a key
   selects is native and is settled by `JustCause3.exe` plus one probe.
5. The EMP/immobiliser half of the gadget set has a **decoded** vehicle use path: the `rebel_emp_01`
   graph's `trigger.use_item` + `entry.use_item` → `S_STUNT_USE_ITEM_VEHICLE` with prompt
   `ui_activate_emp` (`EMP.md` §3). That is the closest system for BmAK's `B`.
6. Eject has **no action name in any of the four keymap copies**; the carrier is the donor exit
   `exit.driver.moving.parachute` → `S_EXIT_VEHICLE_PARA` (gate 5.0–999.0) and Rico's own clip
   `PPparachute_vehicle_eject` — both decoded. The engine's `ACT_EJECT_FROM_VEHICLE` exists with
   **0** data references, so the build authors the exit node rather than waiting for an action.
7. Enter `Y` and exit `LB` are **memory/operator** bindings: the shipped pad table puts enter *and*
   exit on `RPADUP`, and the player's export puts both on `Y`. `Y` is therefore consistent with the
   memory; `LB` is not in either table and is not in BmAK's ini either (`LB` = `DualPlay`,
   `DefaultInput.ini:271`, 0 exit calls).
8. Everything below ends in one of two states: **build edit named** (keymap row, entity node,
   module member, prompt string) or **UNKNOWN with the settling file and a pilot sentence** — never
   "JC3 can't".

---

## 1. The three JC3 systems, as they are on disk

### 1.1 The global action map (`settings/keymap_*.bin`)

| file | layer | archive | entry offset | bytes | bindings | sha256 (16) |
|---|---|---|---:|---:|---:|---|
| `settings/keymap_gamepad.bin` | patch | `patch_win64/game4` | 610914304 | 7,207 | **145** | `0944e37d8588feed` |
| `settings/keymap_keyboard.bin` | patch | `patch_win64/game4` | 610922496 | 5,291 | **104** | `5674c38366c69a85` |
| `settings/keymap_gamepad.bin` | base | `archives_win64/game2` | 2332672 | 6,427 | 131 | `d945f9a02b79d332` |
| `settings/keymap_keyboard.bin` | base | `archives_win64/game5` | 249499648 | 4,615 | 94 | `528f1c6cd82fa33e` |

Decoded shape (`Research/JC3Grab/INPUT.md` §1): an `RTPC` container — root hash `AA7D522A`, one list
node `49267ABC`, then **one 12-byte record per binding** (region `32..1772` = 145 × 12 B), followed
by one inline block per binding: **18 B of property records** (hashes `7935F00C` input / `8613CCD3`
action, both type 3 = `stringZ`) + the literal `"PP"` + whichever of the two names is not already in
the pool, 4-byte aligned. The blocks tile the file exactly (7,207, tail 0) — that tiling is the
oracle that a re-serialise is byte-correct.

| fact | value | label |
|---|---|---|
| bindings / distinct actions | 474 / 154 (all four copies) | decoded |
| binding id = `hash_jenkins(action)` | **448 / 474**; 26 ids are stable but unexplained | decoded/derived |
| land-vehicle action scope | 16 actions: `ACCELERATE`, `REVERSE`, `TURN_LEFT/RIGHT`, `HANDBRAKE`, `ENTER_VEHICLE`, `EXIT_VEHICLE`, `FIRE_VEHICLE_WEAPON_PRIMARY/SECONDARY`, `USE_ITEM`, `USE_VEHICLE_MOD`, `VEHICLE_CAM`, `VEHICLE_RELEASE_GRAPPLE`, `PRECISION_AIM`, `SOUND_HORN_SIREN`, `CHALLENGE_RESET_VEHICLE` | derived (name rule) |
| face buttons in the shipped pad table | **0** (A/B/X/Y absent; controls present are D-pad, sticks, triggers, shoulders, Start/Back) | decoded (`EJECT_MAP.md` §7) |
| tokens on one key | `LSHOULDER` 8, `X` 8 | decoded |
| action ids found in vehicle data | **0 / 134** vehicle `.epe`/`.vmodc`; `keymap` in **0 / 232** entity dumps | decoded (`INPUT_D11.md`) |

**Derived:** the map is global and anonymous to the vehicle — a key is a *row in one table*, and no
entity can scope it. Context separation (enter vs boost on the same button) therefore has to come
from the actions themselves, not from a per-vehicle override.

### 1.2 Weapon and gadget input slots

| fact | value | label |
|---|---|---|
| driver slot pointers on a root class | 4: `main_weapon` (`851CAABE`), `id:00568A74`, `mounted_weapon`, `mounted_weapon_2` | decoded (`WEAPON_WIRING.md` §1) |
| most driver slots on any shipped land entity | **2** (`v0201_car_capstone_mediumtank`, `v0202_…bavariumtank`) | decoded |
| fire actions a vehicle consumes | exactly 2: `FIRE_VEHICLE_WEAPON_PRIMARY` (`RSHOULDER`/`MOUSE1`), `…SECONDARY` (`LSHOULDER`/`MOUSE2`) | decoded (`INPUT.md`) |
| non-fire vehicle-facing actions | `USE_VEHICLE_MOD` (`RPADRIGHT`/`MOUSE3`), `USE_ITEM` (`RPADUP`/`E`), `PRECISION_AIM`, `VEHICLE_RELEASE_GRAPPLE` (`LPADDOWN`/`V`) | decoded |
| active-slot index / next-prev / weapon group in the entity | **none** — "both slots are simply available"; `action_1`/`action_2` are `1`/`2` on armed and unarmed cars alike | decoded (`WEAPON_WIRING.md` §2b) |
| vehicle HUD slots | **2** (`MCI_vehicle_weapons0/1` = `EVEHICLE_WEAPON_SLOT_MAIN`/`_ALTERNATIVE`), via `InitVehicleWeapons(slot_index, weapon_id, weapon_name, infiniteAmmo, magazine_ammo, magazine_size, inventory_ammo, weapon_cooldown, is_overcharged)` (9 args) and `UpdateVehicleWeapons` (6 args); `ShowVehicleSlotAction`/`HideVehicleSlotAction` | decoded (`JC3_HUD_WEAPONS.md` §§1–3) |
| on-foot weapon wheel | `E_NUM_WEAPON_SLOTS = 7` — a different array, not the vehicle's | decoded |
| vehicle use-item path | `trigger.use_item` (`CInteractionTrigger`, `(0, 1.3507, 2.396)`) + `entry.use_item` (`CInteractionGraphEntry`) → `S_STUNT_USE_ITEM_VEHICLE`, prompt `ui_activate_emp` | decoded (`EMP.md` §3) |
| who calls the HUD weapon API | **native** — 2 call sites, both in `TestConstructor`; `UpdateWeaponReticle`/`ShowMissileLocked` have 0 | decoded (`JC3_HUD_WEAPONS.md` §8) |
| usable weapon ids | 69 with `textures/ui/weapon_icons/<id>.ddsc`; **614 has no icon** | decoded |

**Derived:** a gadget's *slot* is data (a root pointer), its *display* is data-limited (2), and its
*selection* is the one thing no file carries.

### 1.3 UI prompts

| fact | value | label |
|---|---|---|
| per-entity prompt table | `…/v0300_car_kensington_sportsmuscle_civilian_01.stringlookup`, **2,226 B** patch / 2,210 B base, 1 entry, hash `A2B9F82C` = **"Get in Vehicle"** | decoded (`NAMES.md` §3) |
| HUD/UI store | `ui/ui_localization.stringlookup` (923,234 B, 11 languages) — holds no vehicle name; it is the lookup for prompt ids | decoded |
| entry prompt member | `entry.use_item.prompt` = `ui_activate_emp` on the EMP truck | decoded (`EMP.md` §3) |
| writer available | `Tools/scripts/jc3strings_write.py IN OUT EDITS.json` — add-only, refuses an existing hash, refuses non-`StringLookup`; writes from the **vanilla patch-layer** file | decoded (tool docstring) |

**Derived:** the enter prompt costs no new work — the vanilla entry already says "Get in Vehicle";
a new prompt (e.g. a winch line) is one added hash, not a new system.

---

## 2. The binding table

`memory` = the control-priority rule (enter `Y`, exit `LB`, everything else BmAK's). "Carrier" is the
member or file that would hold the binding; "build adds" is the edit, not a wish.

| # | binding (BmAK token, key, ini line) | memory rule | closest JC3 system | member / file that carries it | what the build adds | evidence |
|---:|---|---|---|---|---|---|
| 1 | **Drive — accelerate** `aThrottleAxis` / `bFireVehicleWeapon`, **RT** (`252`, `254`) | BmAK | `ACCELERATE` = `RTRIGGER` / `W` — same axis | `settings/keymap_gamepad.bin` (patch) row; `…_land_engine.vmodc`, `…_transmission.vmodc` | no keymap row (RT already `ACCELERATE`); the throttle/boost curves ride the existing modules | **decoded** (both sides) |
| 2 | **Drive — steer** `aTurn`/`aStrafe`, **LS** (`263`, `265`) | BmAK | `TURN_LEFT`/`TURN_RIGHT` = `LSTICKLEFT`/`LSTICKRIGHT` | keymap row; `…_land_steering.vmodc` (`steer_angle_min_speed_deg`, `…max…`, `steering_type` `FrontSteered`, `is_all_wheel_steered` 1) | no keymap row; BmAK's curve numbers are the open value (U6) | **decoded** binding, **UNKNOWN** curve → `sm_default__RVehicleSimBatmobile` / pilot U6 |
| 3 | **Drive — brake / reverse** `BrakePressed` + `bHandbrakeOrBrake`, **X** (`269`) | BmAK | `REVERSE` = `LTRIGGER`/`S`; `HANDBRAKE` = `RPADLEFT`/`LSHIFT` | keymap row; `…_brakes.vmodc` (`handbrake_friction_factor`), `CustomVelocityDamper.handbrake_spin_damping` | **add `REVERSE` + `HANDBRAKE` tokens to X** (multi-token key is the shipped shape), which frees `LT` for the battle hold | **decoded** actions, **derived** edit |
| 4 | **Boost / afterburner** `bVehicleBoostButton`, **Y** (`270`) | BmAK in car | no boost action exists (0 matches `NITRO\|BOOST` except `WINGSUIT_BOOST`); closest = `USE_VEHICLE_MOD` (`RPADRIGHT`/`MOUSE3`) + `arcade.nitro_boost` (145/232) | keymap row; `…_vehicle_misc.vmodc` (`full_nitro_*`), `…_transmission.vmodc` (`nitrous_gears`) | **add `USE_VEHICLE_MOD` to Y** (Y keeps `ENTER_VEHICLE`; `Y`'s enter is inert inside the car by intent) + the nitro members | BmAK **decoded**; JC3 action **UNKNOWN** → settles: `settings/keymap_gamepad.bin` patch + probe U-B1 |
| 5 | **Drift (power slide)** `bHandbrakeOrBrake` + `HandbrakeTurnType` 0x170a, **LS+RT+X** | BmAK | `HANDBRAKE` while `ACCELERATE` held + steer | keymap row; `…_custom_land_global.vmodc` `drift.*` (21 members; fleet defaults `min_speed_to_drift_kmph` 10, `max_drift_torque` 5000, `steering_sensitivity` 4, `max_drift_angle_deg` 45, `counter_steer_torque_handbrake` 30000) | row 3's X edit is the whole input half; the drift block gets BmAK's numbers (T-DR1/T-B4) | **decoded** carrier (C8 "carrier found") |
| 6 | **Eject** `EjectFromVehicle` (+`BattleStrafe`), **A** (`267`) | BmAK | **no `EJECT` action** in any of the four tables; engine `ACT_EJECT_FROM_VEHICLE` has **0** data refs | `.epe` exit nodes: `exit.driver.moving.parachute` → `S_EXIT_VEHICLE_PARA` gate **(5.0, 999.0)**; `exit.driver.roll.out`; `point.driver` `−0.440, 0.340, 0.200` | **author `exit.driver.eject`** on `point.driver` naming `S_EXIT_VEHICLE_PARA`; A already carries `STUNT_JUMP`/`OPEN_PARACHUTE` in the export | **decoded** carrier, **UNKNOWN** first-press semantics → `EJECT_MAP.md` §6.5 |
| 7 | **Glide (eject → glide)** BmAK `_To_Glide` moves | BmAK | `S_EXIT_VEHICLE_PARA` + `OPEN_PARACHUTE`/`OPEN_WINGSUIT` (`RPADUP`/`E`, `LALT`) | `rico_base.afsmb` (`S_EXIT_VEHICLE_PARA` ×2, `ACT_EXIT_VEHICLE` ×1), `rico_base.asb` (`PPparachute_vehicle_eject` 1) | nothing beyond row 6: the glide itself is native; the build only guarantees the state is entered | **decoded** clip/state; **UNKNOWN** 3.73 s lead → `rico_base.afsmb` + probe U-G1 |
| 8 | **Weapons — primary** `BatmobileFireButton` / `bFireVehicleWeapon`, **RT** (`252`) | BmAK | `FIRE_VEHICLE_WEAPON_PRIMARY` = `RSHOULDER`/`MOUSE1` | entity `main_weapon` `851CAABE`; HUD slot 0 `EVEHICLE_WEAPON_SLOT_MAIN` | **add `FIRE_VEHICLE_WEAPON_PRIMARY` to RT** (multi-token with `ACCELERATE`); slot 0 points at a weapon whose id has a shipped icon (≠ 614) | **decoded** |
| 9 | **Weapons — secondary** `SecondaryFireVehicleWeapon` + `PursuitModeTagGun` + `ToggleDrivingCamera`, **RB** (`272`) | BmAK | `FIRE_VEHICLE_WEAPON_SECONDARY` = `LSHOULDER`/`MOUSE2`; `VEHICLE_CAM` = `RSTICKBUTTON`/`B` | entity `id:00568A74`; HUD slot 1 `EVEHICLE_WEAPON_SLOT_ALTERNATIVE` | **add `FIRE_VEHICLE_WEAPON_SECONDARY` + `VEHICLE_CAM` to RB**, and **remove `FIRE_VEHICLE_WEAPON_SECONDARY` from `LSHOULDER`** (LB is exit) | **decoded** |
| 10 | **Gadget slot 1** (tracker / immobiliser / EMP) `QuickGadgetB` → `SelectVehicleWeapon(1)`, **B** (`268`) | BmAK | `USE_ITEM` (`RPADUP`/`E`) + the EMP truck's `trigger.use_item`/`entry.use_item` → `S_STUNT_USE_ITEM_VEHICLE` | `.epe` interaction graph (copy `trigger.use_item` + `entry.use_item` from `rebel_emp_01`); prompt `ui_activate_emp`; `CForcePulse` (`truck_emp.ftune`, flags `4912FC04` 0 / `AE6F7EFF` 1 / `CF4F7880` 1) | **add `USE_ITEM` to B**, copy the two interaction objects, and give the gadget its own `main_weapon` slot for the launch half (T-WP9/B-21) | **decoded** graph path; **UNKNOWN** what `USE_ITEM` does in a car → `INPUT_D11.md` #3 + probe U-G2 |
| 11 | **Gadget slot 2** (missile barrage) `QuickGadgetX` → `SelectVehicleWeapon(2)`, **X** (`269`) | BmAK | `USE_VEHICLE_MOD` (`RPADRIGHT`/`MOUSE3`) — the only vehicle "mod" action | entity root pointer (2nd slot free); `…_transmission.vmodc`? no — the slot is the entity | **add `USE_VEHICLE_MOD` to X** (X also carries `HANDBRAKE`/`REVERSE`); the salvo needs `missile_per_shot` > 1, which no tune has (B-24) | **UNKNOWN** — the action name is decoded, the *slot index* is not; settles: `JustCause3.exe` keymap consumer + probe U-G3 |
| 12 | **Gadget slot 3** (drone virus) `QuickGadgetY` → `SelectVehicleWeapon(3)`, **Y** (`270`) | BmAK | same as row 11 (`USE_VEHICLE_MOD`) | entity root pointer; hacker chain B-19 (`SAttachedEffect`, `CInteractionGraph` context-act) | **add `USE_VEHICLE_MOD` to Y** alongside `ENTER_VEHICLE` and the boost token (three tokens, one key — `LSHOULDER` carries 8) | **UNKNOWN** slot index → as row 11 |
| 13 | **Gadget slot 4** (missile pods) `SelectVehicleWeapon 4`, **D-Pad Up** (`259`) | BmAK | no action; `PursuitModeWeapons[10]` is BmAK's own array | entity 4th pointer (`mounted_weapon` / `id:AC0BC788`); missile sockets `MissileL`/`MissileR` | **add a fourth action row** (`USE_VEHICLE_MOD` on `LPADUP`) and point the two null pointers at the pod weapon | **UNKNOWN** → as row 11 |
| 14 | **Sonar** `BatmobileSonar` → `…Pressed`/`…Released`, **L3** (`256`) | BmAK | no `SONAR`/`SCAN` action; closest = `CForcePulse` (`gen_explosion_5m_nodamage.ftune`) + `BML_Sonar` bank + `CreatePoi` | entity `CForcePulse` + `CMaterialEffectTable`; `BmGame.BML_Sonar` (355,830 B, 6 verified events) | **add a spare action row on `LSTICKBUTTON`** and B-20's pulse/ring/POI | **UNKNOWN** input → `INPUT.md` §UNKNOWN + probe U-S1 |
| 15 | **Enter** — memory **Y** (BmAK has no enter token at all) | memory `Y` | `ENTER_VEHICLE` — shipped table `RPADUP`, player export **`Y`**, 0 face buttons shipped | keymap row; `.epe` `entry.driver` → `S_ENTER_DRIVER_VEHICLE` (`check` 0, `min` 0, `max` 3); prompt `A2B9F82C` "Get in Vehicle"; `point.driver` transform | **add `Y → ENTER_VEHICLE`** to the patch keymap; no `.epe` change (all three objects already exist in the mod's own file) | memory + export **decoded**; shipped table **UNKNOWN** → `settings/keymap_gamepad.bin` + probe U-E1 |
| 16 | **Exit** — memory **LB** (BmAK menu label; `ExitVehiclePressed` absent from `BmGame.upk`) | memory `LB` | `EXIT_VEHICLE` (shipped `RPADUP`, export `Y`) | keymap row; `.epe` `exit.driver.default` → `S_EXIT_VEHICLE`; `exit.driver.moving.parachute` for a moving exit | **add `LSHOULDER → EXIT_VEHICLE`**, drop `FIRE_VEHICLE_WEAPON_SECONDARY` from `LSHOULDER`; add `exit.driver.side` for `bCanGetOutOnLeftSide` | memory **UNKNOWN** in every file → `CONTROLS_CONSUMERS.md` §4 (`LB`=`DualPlay`, 0 exit calls) + probe U-E2 |

Rows 1–9 and 15–16 are the memory set; rows 10–14 are the gadget/weapon inputs the report left open.

---

## 3. Evidence notes (only where a label needs showing)

**3.1 Why "enter `Y`" is consistent, not a conflict.** The shipped pad table binds **no face
button** and puts enter *and* exit on `RPADUP`; the player's export (`kepmap.txt`, 249 rows) puts
both on **`Y`** (`EJECT_MAP.md` §5). BmAK's ini has **no enter token at all** (`CONTROLS.md`: 30
vehicle rows, none an enter) and its `ExitVehicle` alias at `DefaultInput.ini:178` is referenced by
**0** key lines. So `Y` is the only button either side offers, and the *only* edit the memory rule
forces is the **split of the shared enter/exit pair** — in the shipped table one control would both
enter and exit.

**3.2 Why `LB` needs a script route, not an ini route.** `DefaultInput.ini:271` binds
`XboxTypeS_LeftShoulder` to `DualPlay` → `DualPlayPressed` (17 script bytes, 0 virtual/final calls
to an exit function), and `ExitVehiclePressed` is not in `BmGame.upk`'s name table. `LB` therefore
cannot be an ini binding in BmAK either; the operator's live observation (`GRAB_BACKLOG.md` D-11)
is the only evidence it exits, and the member that would carry it on the JC3 side is the exit node,
not the ini.

**3.3 Why boost and enter can share `Y`.** Binding id = `hash_jenkins(action)` and a key carries a
*list* of tokens; `LSHOULDER` and `X` each carry **8** in shipped data. `ENTER_VEHICLE` is only
offered at a vehicle prompt and `USE_VEHICLE_MOD` only from inside one, so the two actions can live
on the same row without a per-entity scope. This is a **derived** composition; the runtime half is
probe U-E1.

**3.4 Why gadget selection is the hard row.** JC3's vehicle slots have **4 pointers, 2 fire actions,
2 HUD slots and no index** (`WEAPON_WIRING.md` §2b: "there is no active-slot index, no next/previous
weapon action and no weapon group anywhere in the `.epe`"). BmAK's `SelectVehicleWeapon(1..4)`
(handler export 105040, 10 script bytes; gate chain in export 104971) has no JC3 member. The build
can ship **8 slots** (`T-WP13`: 4 `CCar` roots × `main_weapon` + `id:00568A74`) and the four
engine-named actions (`FIRE_VEHICLE_WEAPON_PRIMARY`, `…SECONDARY`, `USE_VEHICLE_MOD`, `USE_ITEM`);
what it cannot do from data is decide *which* slot a key selects. That single unknown is stated once
in §5 (U-G3) rather than repeated per row.

**3.5 Eject has a carrier but no action.** `review-JC3-EJECT.md`: `ACT_EJECT_FROM_VEHICLE` and
`ACT_EJECT_FROM_VEHICLE_MG` are in `JustCause3.exe` at `0x23d4528`/`0x23d4540` with **0** references
in any `.afsmb`; `ACT_EXIT_VEHICLE` (the control) is in 3. The donor's `exit.driver.moving.parachute`
(`S_EXIT_VEHICLE_PARA`, gate 5.0–999.0) and Rico's `PPparachute_vehicle_eject` clip are decoded, so
the build **authors the exit node** and does not need the unreferenced action.

**3.6 Prompt coverage.** The mod's `.stringlookup` copy is **2,210 B, byte-identical to the vanilla
base copy**; the patch copy (2,226 B) differs only in padding. Enter therefore keeps the vanilla
"Get in Vehicle" string; a new prompt is one `jc3strings_write.py` edit from the vanilla patch file
(add-only, existing hash refused).

---

## 4. Build composition

New private tree `Builds/bm-RC4-controls/`, based on `Builds/bm-RC4` (the assembled RC: entity +
weapons + handling + effects + audio + rebel). Three legs, each removable alone.

### Leg 1 — the action map (`settings/keymap_*.bin`)

Two new files in the drop tree, copied from the **vanilla patch layer** and re-serialised with
`Tools/scripts/jc3_input.py`'s reader/writer pair (the same tiling oracle: 18 B property block +
`"PP"`+strings, 0–3 tail bytes):

| file | bindings (vanilla patch) | rows changed / added (final count fixed by the tiling oracle at write time, not stated here) |
|---|---:|---|
| `settings/keymap_gamepad.bin` | **145** | `Y`: `ENTER_VEHICLE` + `USE_VEHICLE_MOD` (new row — the shipped table has no face button); `LSHOULDER`: `EXIT_VEHICLE` added, `FIRE_VEHICLE_WEAPON_SECONDARY` removed; `X`: `HANDBRAKE` + `REVERSE` (new row); `B`: `USE_ITEM` (new row); `RB` (= `RSHOULDER`): `FIRE_VEHICLE_WEAPON_SECONDARY` + `VEHICLE_CAM`; `RT`: `FIRE_VEHICLE_WEAPON_PRIMARY`; `LPADUP`: `USE_VEHICLE_MOD`; `LSTICKBUTTON`: spare scan action |
| `settings/keymap_keyboard.bin` | **104** | the same actions on the keyboard keys `INPUT.md` already assigns (`E`, `LSHIFT`, `S`, `MOUSE1`, `MOUSE2`, `V`, `LALT`), plus one scan key |

Registration: `@files.xml` (B-18 pattern) — the drop tree already ships a `settings/*.bin`
(`settings/spawn_vehicle_defs.bin` from `bm-RC4-rebel`, `bm_rc4.py` `DROP_SRC`), so the path class is
precedented. Reversibility: delete the two files; the vanilla patch copies win again.

### Leg 2 — the entity (`.epe`)

Merged into the RC4 `.epe` with `bm_rc4.py`'s `git merge-file` on the `ConvertProperty` XML (base =
the parts tree's `.epe`; a conflict stops the build):

1. `exit.driver.eject` — a new `Exit` node on `point.driver` naming `S_EXIT_VEHICLE_PARA`
   (row 6); `exit.driver.side` for `bCanGetOutOnLeftSide` (row 16).
2. `trigger.use_item` + `entry.use_item` — copied from `rebel_emp_01` with `prompt`
   `ui_activate_emp` and state `S_STUNT_USE_ITEM_VEHICLE` (row 10).
3. Four `CCar` roots with `main_weapon` (`851CAABE`) + `id:00568A74` non-null = **8 slots**
   (`T-WP13`), the two gunner pointers left null; re-read must show 8 non-null ids, 0 dangling.
4. Additions go through `Working/Entity/bm_epe_edits.json` and the B-05 writer; the receipt records
   object count, slot ids and the new node names.

### Leg 3 — the carrier members

| file (private, under `modules/default/batmobile/`) | members the controls need |
|---|---|
| `…_custom_land_global.vmodc` | `drift.max_drift_torque`, `constant_drift_torque`, `min_speed_to_drift_kmph`, `steering_sensitivity`, `max_drift_angle_deg`, `counter_steer_torque_handbrake`, `drift_*_vel_damp`, `velocity_rotation_amount/start/end` (row 5) |
| `…_brakes.vmodc` | `handbrake_friction_factor`; `CustomVelocityDamper.handbrake_spin_damping` (row 3) |
| `…_land_steering.vmodc` | `steer_angle_min_speed_deg` / `…max…`, `steering_type`, `is_all_wheel_steered` (row 2) |
| `…_vehicle_misc.vmodc` | `full_nitro_*` (row 4) |
| `…_transmission.vmodc` | `nitrous_gears` (row 4) |
| `…_land_audio.vmodc` | cockpit open/close events (rows 15/16, U4 in the entry plan) |

HUD: `ui/hud.gfx` is **not** a build target (native caller, 0 movie call sites), so the build ships
weapon ids that resolve (`textures/ui/weapon_icons/<id>.ddsc`, 69 ids; **614 excluded**) and accepts
the 2-slot display limit — the extra six slots are selected, not drawn. That limit is the existing
`T-HUD5` row, cited, not re-opened.

### Prompt leg (if a new prompt is ever needed)

`jc3strings_write.py <vanilla patch .stringlookup> <out> edits.json` — add-only. The enter prompt is
not needed (vanilla `A2B9F82C`), so this leg ships **no** string edit unless a new interaction entry
is added.

### Offline checks before any launch

| check | command | pass |
|---|---|---|
| keymap tiles (both devices) | `python -I Tools/scripts/jc3_input.py --check` | 145/104 base rows reproduced; new files tile with 0–3 tail bytes and the same string-pool dedupe |
| action ids are `H(name)` | `rbmhdr.hash_jenkins(action)` per new row | every added id equals the hash of its action (the 448/474 rule) |
| `.epe` slot count | `python Tools/scripts/bm_entity.py --check` | 8 non-null slot ids, 0 dangling, new node names present |
| prompt table decodes | `python Tools/scripts/jc3strings.py --check` | 1 entry, `A2B9F82C` = "Get in Vehicle" unchanged |
| `.toc` internal | `eetoc.py verify` / `aafdiff` | record offset ≠ 0, size matches, file count +2 |
| receipt | RC4 `receipt.json` schema 2 | sha256/bytes/offset per file, rows table, revert line |
| tamper | flip one key name, one slot id, force `.toc` offset 0 | each caught and reverted |

---

## 5. UNKNOWNs — each with the file that settles it and one pilot sentence

| # | unknown | settles with | pilot-card sentence (pass band) |
|---|---|---|---|
| U-E1 | which table the game loads (shipped `RPADUP` enter/exit vs export `Y`) and whether a dropzone keymap is honoured at all | `settings/keymap_gamepad.bin` patch entry (145 records) + `INPUT.md` §UNKNOWN; runtime probe | Stand 2 m from the parked car and press `Y`: the "Get in Vehicle" prompt must vanish and Rico must be seated within the 0.433 s entry clip **3/3**, and a second `Y` press must not exit **3/3**. |
| U-E2 | whether `LB` exits at all (BmAK binds it to `DualPlay`; JC3 binds it to secondary fire) | `CONTROLS_CONSUMERS.md` §4 (`DualPlayPressed`, 17 B, 0 exit calls) + the new keymap row | With the car stopped press `LB`: Rico must leave via `S_EXIT_VEHICLE` **3/3**; at 60 km/h the same press must route to `S_EXIT_VEHICLE_PARA` **3/3**, never a standing exit. |
| U-B1 | which action actually fires the afterburner (no `NITRO`/`BOOST` action exists; `arcade.nitro_boost` is on 145/232 cars) | `INPUT.md` §UNKNOWN + `settings/keymap_*.bin` probe on `USE_VEHICLE_MOD` | In pursuit hold `Y`: speed must exceed the no-boost top speed by `extra_top_speed` for `BoostDuration` then fall back, with the nitrous FX firing **3/3**. |
| U-G2 | what `USE_ITEM` does inside a car (0/134 vehicle modules reference it; the only decoded use is the EMP truck's graph) | `INPUT_D11.md` #3 + `JustCause3.exe` keymap consumer | Park beside a drone and press `B`: the `ui_activate_emp` prompt must appear **3/3** and the EMP pulse must stall the target **2/3**, with no weapon firing. |
| U-G3 | which slot a gadget key selects (no active-slot index, no next/prev action in any `.epe`) | `WEAPON_WIRING.md` §2b + `JustCause3.exe` native consumer; the build ships 8 slots regardless | Tap `X` then `RT` twice: the second shot must come from the slot-`X` weapon **3/3** (barrage), and the HUD slot 1 label must change to it. |
| U-S1 | the sonar trigger (no `SONAR`/`SCAN` action in any of the four tables) | `INPUT.md` §UNKNOWN + keymap probe on `LSTICKBUTTON` | Press `L3` with a target 20 m away behind a wall: a scan visual must appear **3/3**, or **0/3** with the row re-queued (no silent pass). |
| U-G1 | the 3.7333 s eject→glide lead (BmAK; JC3 enters `S_EXIT_VEHICLE_PARA` at the exit) | `rico_base.afsmb` (state ×2) + the `PPparachute_vehicle_eject` clip length (not decoded) | Eject at 60 km/h over flat ground: `OPEN_WINGSUIT` must be accepted within **0.2 s** of the para state and the descent must end in a landing **3/3**. |
| U6 | BmAK's steering curve (`aTurn` has no decoded values) | `sm_default__RVehicleSimBatmobile` (`StandardSteeringSpeedCurve`, `DesiredTurnOnSpotSpeed`) | Hold full left at 30 and 120 km/h: the 90° heading-change times must sit in a **1.6–2.4** ratio with no wheel-lock below 10 km/h. |

---

## 6. Sources

- `tmp/freebuff/reports/bmak-control-scheme-storage.md` — the BmAK side: the ini chain, the
  `DefaultInput.ini` lines (`252`–`272`), the 0-hit save census, the two installs diffed.
- `Research/BatmobileGrab/CONTROLS.md` — 374 bindings, token→key→line, alias table, `DrivingMode`
  consumers.
- `Research/BatmobileGrab/CONTROLS_MENU_SCREENS.md` — the drawn labels (pursuit + battle) and the
  operator block: enter `Y`, exit `LB`, pause/commlink keep JC3 priority.
- `Research/BatmobileGrab/CONTROLS_CONSUMERS.md` §1/§2/§4/§5 — `LT` threshold, `B`, `LB`=`DualPlay`,
  `A` eject.
- `GRAB_BACKLOG.md` D-11 — the control-priority decision; D-3 (riot mode omitted); D-7.
- `Research/JC3Grab/INPUT.md` — 474 bindings / 154 actions, the four keymap files, the tiling oracle,
  the `H(name)` id rule, the 0/134 and 0/232 censuses, the per-class action sets, the 16 land-vehicle
  actions, and the UNKNOWNs this plan cites.
- `Research/JC3Grab/INPUT_D11.md` — `USE_ITEM` name-only, 0 vehicle consumers.
- `Research/JC3Grab/EJECT_MAP.md` §§4–7 — per-button ownership, the shipped (`RPADUP`) vs export
  (`Y`) divergence, 0 face buttons, 8-token keys, 24 checks.
- `Research/JC3Grab/SEAT.md` §§1–2 — `entry.driver`, `point.driver`, the exit family, `MOD_LOW`.
- `Research/JC3Grab/WEAPON_WIRING.md` §1/§2 — four slot pointers, `851CAABE`, `id:00568A74`,
  "no active-slot index / no switch action".
- `Research/JC3Grab/JC3_HUD_WEAPONS.md` §§1–3, §7–8 — 2 vehicle HUD slots, the 9/6-arg API,
  `ShowVehicleSlotAction`, native caller, icon ids (614 missing).
- `Research/JC3Grab/EMP.md` §3, §7–8 — `trigger.use_item`/`entry.use_item` →
  `S_STUNT_USE_ITEM_VEHICLE`, prompt `ui_activate_emp`, the pulse flags.
- `Research/JC3Grab/NAMES.md` §3 — the entity `.stringlookup`, `A2B9F82C` "Get in Vehicle".
- `Research/JC3Grab/DRIVE_CARRIERS.md` C1/C8/C9 — drift/nitro carriers and fleet defaults.
- `tmp/freebuff/reports/entry-exit-and-controls-plan.md` — the entry/exit/canopy composition this
  plan's rows 6/7/16 build on; `tmp/freebuff/reports/eject-and-glider-landing-plan.md` — eject/glide.
- `tmp/freebuff/reports/apply-weapon-slot-rows.md` (T-WP13, T-WP4), `apply-gadget-rows.md`
  (B-18…B-21) — the slot and gadget builds this plan's rows 10–14 rely on.
- `Working/Q/PILOT/CONTROLS.md` — the 24-row master table and conflicts A–H.
- `Tools/scripts/jc3_input.py`, `jc3strings_write.py`, `bm_rc4.py`, `bm_entity.py`,
  `bm_leaf.py`, `eetoc.py` — the readers/writers the build legs use.

## 7. What was checked here, and what was not

Checked (offline, read-only): every BmAK line cited; the four keymap files' size/offset/binding
counts; the 0-face-button and 8-token-key facts; the slot-pointer and HUD-slot facts; the prompt
entry hash and byte sizes; the mod's `.stringlookup`/`.epe` paths in `Builds/bm-RC4-entity` (found on
disk); the RC4 assembler's `DROP_SRC` (a `settings/*.bin` precedent).

Not done, by scope: no keymap re-serialise, no `.epe` edit, no module write, no string write, no
install, no game launch (`APPROVED_Q.txt` absent), no ledger or backlog edit. Every number above is
read from a file or derived from one; none is a measurement from a running game.
