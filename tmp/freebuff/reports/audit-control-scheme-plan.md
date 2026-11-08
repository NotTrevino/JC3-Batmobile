# Audit — `control-scheme-closest-system-plan.md`

Audit date: 2026-11-07. Audited file: `tmp/freebuff/reports/control-scheme-closest-system-plan.md`
(315 lines, unmodified). This audit is read-only against the plan.

Scope: every factual figure in the plan — binding counts, byte sizes, offsets, hashes,
action names, controller tokens, entity member paths, HUD-slot counts, script byte counts,
durations and per-key token counts — checked against the file the plan cites at that point.
Line numbers are from `nl -ba` on each file as it exists on disk today.

Method: for each claim I opened the cited file, found the line that carries the same value,
and copied that value into the table. Where the cited file states a different or narrower
value, the verdict is OVERSTATED. Where the cited file does not carry the figure at all,
the verdict is UNSUPPORTED (a source exists but does not say it) or UNKNOWN (no citable
source; the settling file is named). No game install, GOG folder or save file was opened;
the BmAK install paths in the plan and in `bmak-control-scheme-storage.md` were not touched.

Verdict legend:

- **VERIFIED** — the cited file states the same value on the line shown.
- **OVERSTATED** — the cited file states a different, narrower or qualified value.
- **UNSUPPORTED** — the figure is not in any cited file, and the available data undercuts it.
- **UNKNOWN** — no citable source states the figure; the file that would settle it is named.

Summary: **80 figures audited — 67 VERIFIED, 9 OVERSTATED, 1 UNSUPPORTED, 3 UNKNOWN.**
The plan's core JC3 numbers (keymap table, slot model, HUD API, EMP graph, prompt table)
hold up. The failures cluster in the BmAK binding-derived rows (steering stick, token
counts, drift member count, glide keys), in two misattributed export ids, and in three
figures that only a prior plan or the running game can settle.

| Claim | Plan line | Source file and line | Source value | Verdict |
|---|---|---|---|---|
| Gamepad **patch** keymap: 145 bindings, 7,207 B, entry offset 610,914,304, sha256 `0944e37d8588feed` | 57 (also 21, 200, 247) | `Research/JC3Grab/INPUT.md:14` (record region `:25`) | `patch / patch_win64/game4 / 610914304 / 7207 / 145 / 0944e37d8588feed` | VERIFIED |
| Keyboard **patch** keymap: 104 bindings, 5,291 B, entry offset 610,922,496, sha256 `5674c38366c69a85` | 58 | `Research/JC3Grab/INPUT.md:16` (record region `:27`) | `patch / patch_win64/game4 / 610922496 / 5291 / 104 / 5674c38366c69a85` | VERIFIED |
| Gamepad **base** keymap: 131 bindings, 6,427 B, entry offset 2,332,672, sha256 `d945f9a02b79d332` | 59 | `Research/JC3Grab/INPUT.md:13` (record region `:24`) | `base / archives_win64/game2 / 2332672 / 6427 / 131 / d945f9a02b79d332` | VERIFIED |
| Keyboard **base** keymap: 94 bindings, 4,615 B, entry offset 249,499,648, sha256 `528f1c6cd82fa33e` | 60 | `Research/JC3Grab/INPUT.md:15` (record region `:26`) | `base / archives_win64/game5 / 249499648 / 4615 / 94 / 528f1c6cd82fa33e` | VERIFIED |
| One 12-byte record per binding; patch record region `32..1772` = 145 × 12 B | 63 | `Research/JC3Grab/INPUT.md:25` | `32..1772 (145 x 12 B) / 145 bindings` | VERIFIED |
| Each binding owns 18 B of property records; hashes `7935F00C` input / `8613CCD3` action; both type 3 (`stringZ`); literal `"PP"` prefix | 64–65 | `Research/JC3Grab/INPUT.md:20,29` | `18 B of property records`; `7935F00C / 8613CCD3`; `every property is type 3 (stringZ)` | VERIFIED |
| Keymap container: RTPC root hash `AA7D522A`, one list node `49267ABC` | 62–63 | `Research/JC3Grab/INPUT.md:33` | `Root hash AA7D522A and list hash 49267ABC` | VERIFIED |
| Binding blocks tile the 7,207-byte patch file with tail 0 | 66 | `Research/JC3Grab/INPUT.md:25` | `tiled end 7207 / tail 0 / tiles True` | VERIFIED |
| 474 bindings across four copies; 154 distinct action names | 71 | `Research/JC3Grab/INPUT.md:31,35` | `of 474 bindings`; `474 rows over 4 files; 154 distinct action names` | VERIFIED |
| Binding id equals `H(action)` on 448 of 474; 26 ids unexplained | 72 | `Research/JC3Grab/INPUT.md:31,291` | `equals action 448`; `why 26 binding ids are not H(action name)` | VERIFIED |
| Land-vehicle scope is exactly 16 named actions | 73 | `Research/JC3Grab/INPUT.md:223` | The 16-row `land-vehicle` list, same names | VERIFIED |
| Shipped gamepad table has 0 face-button rows (no A/B/X/Y) | 24, 74, 144 | `Research/JC3Grab/EJECT_MAP.md:69,145` | `binds no face button at all (0 rows for A/B/X/Y)`; `face-button rows: 0` | VERIFIED |
| `LSHOULDER` carries 8 tokens, including `FIRE_VEHICLE_WEAPON_SECONDARY` | 26, 29, 75, 160 | `Research/JC3Grab/EJECT_MAP.md:148` | `shipped ['DEV_MODIFIER_COMBO_1', 'FIRE_GRAPPLE', 'FIRE_VEHICLE_WEAPON_SECONDARY', 'FREEFLY_COMBO1', 'GUI_TAB_PREV', 'L1', 'MC_RELOAD', 'MECH_PUNCH']` | VERIFIED |
| `X` carries 8 tokens in shipped data | 29, 75 | `Research/JC3Grab/EJECT_MAP.md:69,116,148`; `Research/JC3Grab/INPUT.md:185` | No X count exists; shipped pad has no X row; export X carries 3 (`FIRE_WINGSUIT_WEAPON_SECONDARY`, `HANDBRAKE`, `RELOAD`); keyboard X carries 1 (`SOUND_HORN_SIREN`) | UNSUPPORTED |
| The only BmAK button that collides with a JC3 token is `LB` | 24–26 | `Research/JC3Grab/EJECT_MAP.md:112–121` | B displaces `USE_VEHICLE_MOD` (:115); RB displaces primary fire (:117); LT displaces `REVERSE` (:119); LS press displaces horn (:120); X conflicts with `HANDBRAKE` (:116) | OVERSTATED |
| Action ids in vehicle data: 0/134 `.epe`/`.vmodc`; `keymap` in 0/232 entity dumps | 76 | `Research/JC3Grab/INPUT_D11.md:5,70,72` | `134 decoded vehicle .epe/.vmodc files`; `0 files`; `USE_ITEM ... keymap 0/232` | VERIFIED |
| Four driver/gunner slot pointers: `main_weapon` (`851CAABE`), `id:00568A74`, `mounted_weapon`, `mounted_weapon_2` | 86 | `Research/JC3Grab/WEAPON_WIRING.md:11–14` | Same four-row slot table | VERIFIED |
| Most driver slots on a shipped land entity is 2 (`v0201_car_capstone_mediumtank`, `v0202_...bavariumtank`) | 87 | `Research/JC3Grab/WEAPON_WIRING.md:26` | `Two driver slots are wired on v0201_car_capstone_mediumtank, v0202_car_capstone_bavariumtank` | VERIFIED |
| Exactly 2 fire actions: `FIRE_VEHICLE_WEAPON_PRIMARY` (`RSHOULDER`/`MOUSE1`), `...SECONDARY` (`LSHOULDER`/`MOUSE2`) | 88 | `Research/JC3Grab/INPUT.md:78–79` | Same two rows and bindings | VERIFIED |
| Non-fire vehicle actions: `USE_VEHICLE_MOD` (`RPADRIGHT`/`MOUSE3`), `USE_ITEM` (`RPADUP`/`E`), `PRECISION_AIM`, `VEHICLE_RELEASE_GRAPPLE` (`LPADDOWN`/`V`) | 89 | `Research/JC3Grab/INPUT.md:167,195,196,198` | Same names and bindings | VERIFIED |
| No active-slot index / next-prev action / weapon group; `action_1`/`action_2` are `1`/`2` on armed and unarmed cars | 90 | `Research/JC3Grab/WEAPON_WIRING.md:31` | `there is no active-slot index, no next/previous weapon action and no weapon group anywhere in the .epe`; `action_1/action_2 are 1/2` | VERIFIED |
| Vehicle HUD has 2 slots: `MCI_vehicle_weapons0/1` = `EVEHICLE_WEAPON_SLOT_MAIN`/`_ALTERNATIVE` | 91 | `Research/JC3Grab/JC3_HUD_WEAPONS.md:56` | `2 slots (MCI_vehicle_weapons0, MCI_vehicle_weapons1), indexed 0 = EVEHICLE_WEAPON_SLOT_MAIN and 1 = EVEHICLE_WEAPON_SLOT_ALTERNATIVE` | VERIFIED |
| `InitVehicleWeapons` takes 9 args; `UpdateVehicleWeapons` takes 6 | 91 | `Research/JC3Grab/JC3_HUD_WEAPONS.md:5,14,34,217` | `9 arguments`; `6`; full 9-arg and 6-arg signatures | VERIFIED |
| `E_NUM_WEAPON_SLOTS = 7` is the on-foot wheel, not the vehicle array | 92 | `Research/JC3Grab/JC3_HUD_WEAPONS.md:56` | `E_NUM_WEAPON_SLOTS = 7, which is the on-foot weapon wheel` | VERIFIED |
| EMP path: `trigger.use_item` at `(0, 1.3507, 2.396)`, `entry.use_item` → `S_STUNT_USE_ITEM_VEHICLE`, prompt `ui_activate_emp` | 93 | `Research/JC3Grab/EMP.md:80–82` | Same state, prompt and trigger position | VERIFIED |
| HUD weapon API: 2 call sites, both in `TestConstructor`; `UpdateWeaponReticle` and `ShowMissileLocked` have 0 | 94 | `Research/JC3Grab/JC3_HUD_WEAPONS.md:202–204,209` | `InitVehicleWeapons ... 2 ... TestConstructor`; `UpdateVehicleWeapons ... 0`; `UpdateWeaponReticle ... 0`; `ShowMissileLocked/HideMissileLocked have none` | VERIFIED |
| 69 usable weapon icon ids; id 614 has no icon | 95, 233 | `Research/JC3Grab/JC3_HUD_WEAPONS.md:159,162` | `69 distinct icon ids`; `without an icon: 614` | VERIFIED |
| Entity prompt table: 2,226 B patch / 2,210 B base, 1 entry, hash `A2B9F82C` = "Get in Vehicle" | 104 | `Research/JC3Grab/NAMES.md:75,80,86` | `2226 B ... 1 entry`; `A2B9F82C / Get in Vehicle`; `2210 B, byte-identical to the base copy` | VERIFIED |
| UI store `ui/ui_localization.stringlookup` is 923,234 B, 11 languages, holds no vehicle name | 105 | `Research/JC3Grab/NAMES.md:89` | `ui/ui_localization.stringlookup (923,234 B, 11 languages ...) does not hold the name` | VERIFIED |
| `jc3strings_write.py` is add-only, refuses an existing hash, refuses a non-StringLookup layout, writes from the vanilla patch-layer file | 107 | `Tools/scripts/jc3strings_write.py:24–31` | `A hash that already exists ... is refused (this tool only adds)`; layout `checked at run time, refused otherwise`; `Always write from the VANILLA patch-layer file` | VERIFIED |
| RT: `aThrottleAxis` at `DefaultInput.ini:254`, `bFireVehicleWeapon` at `:252` | 121 | `Research/BatmobileGrab/CONTROLS.md:47,68` | `BatmobileFireButton ... :252`; `aThrottleAxis ... :254 XboxTypeS_RightTriggerAxis` | VERIFIED |
| Steering `aTurn`/`aStrafe` is on **LS**, lines 263/265 | 122 | `Research/BatmobileGrab/CONTROLS.md:67,69` | `aStrafe ... XboxTypeS_LeftX ... :263`; `aTurn ... XboxTypeS_RightX ... :265` | OVERSTATED |
| `REVERSE` = `LTRIGGER`/`S`; `HANDBRAKE` = `RPADLEFT`/`LSHIFT` | 123 | `Research/JC3Grab/INPUT.md:114,178` | Same two rows | VERIFIED |
| `BrakePressed` + `bHandbrakeOrBrake` are on X at line 269 | 123 | `Research/BatmobileGrab/CONTROLS.md:49,73` | Both tokens: `XboxTypeS_X ... :269` | VERIFIED |
| `bVehicleBoostButton` is on Y at line 270; no NITRO/BOOST action exists except `WINGSUIT_BOOST` | 124 | `Research/BatmobileGrab/CONTROLS.md:76`; `Research/JC3Grab/INPUT.md:274` | `bVehicleBoostButton ... XboxTypeS_Y ... :270`; regex result `['WINGSUIT_BOOST']` | VERIFIED |
| `arcade.nitro_boost` appears on 145 of 232 cars | 124, 263 | `Research/JC3Grab/INPUT.md:234` | `arcade.nitro_boost / 145` | VERIFIED |
| Power slide binding is left stick + RT + X | 125 | `Research/BatmobileGrab/CONTROLS_MENU_SCREENS.md:19` | `left stick + RT + X / Power Slide` | VERIFIED |
| `CustomLandGlobal.drift.*` block has 21 members | 125 | `Research/JC3Grab/DRIVE_CARRIERS.md:111` (also `:27`) | `a 20-member block on 145 builds` | OVERSTATED |
| Drift fleet defaults: 10 / 5000 / 4 / 45 / 30000 | 125 | `Research/JC3Grab/DRIVE_CARRIERS.md:117–122` | `min_speed_to_drift_kmph 10`, `max_drift_torque 5000`, `steering_sensitivity 4`, `max_drift_angle_deg 45`, `counter_steer_torque_handbrake 30000` | VERIFIED |
| `HandbrakeTurnType` is offset `0x170a` | 125 | No decoded file: `Research/JC3Grab/VOCABULARY.md` (member paths) and `Research/JC3Grab/DRIVE_CARRIERS.md` §9 (decoded `land_global`) would settle it | No line states `0x170a`; only the earlier `tmp/freebuff/reports/entry-exit-and-controls-plan.md:232` restates it | UNKNOWN |
| `EjectFromVehicle` + `BattleStrafe` are on A at line 267 | 126 | `Research/BatmobileGrab/CONTROLS_CONSUMERS.md:256` | `XboxTypeS_A ... :267` command includes `EjectFromVehicle / BattleStrafe` | VERIFIED |
| `exit.driver.moving.parachute` → `S_EXIT_VEHICLE_PARA` with gate `(5.0, 999.0)` | 126, 177 | `Research/JC3Grab/EJECT_MAP.md:77,150` | `gate (5.0, 999.0)`; `that exit's only gate is a parent-speed gate 5..999` | VERIFIED |
| `point.driver` is at `-0.440, 0.340, 0.200` | 126 | `Research/JC3Grab/SEAT.md:25` | `-0.440, 0.340, 0.200` | VERIFIED |
| No `EJECT` action in the four tables; `ACT_EJECT_FROM_VEHICLE` has 0 data references | 126 | `Research/JC3Grab/INPUT.md:268`; `tmp/freebuff/reports/review-JC3-EJECT.md:144–145` | `actions matching /EJECT/: 0`; `ACT_EJECT_FROM_VEHICLE ... .afsmb 0 distinct files 0` | VERIFIED |
| A already carries `STUNT_JUMP` / `OPEN_PARACHUTE` in the export | 126 | `Research/JC3Grab/EJECT_MAP.md:51–52` | Both `export = A` | VERIFIED |
| Glide keys: `OPEN_PARACHUTE`/`OPEN_WINGSUIT` = `RPADUP`/`E`, `LALT` | 127 | `Research/JC3Grab/INPUT.md:156,157,202` | `OPEN_PARACHUTE / RPADDOWN / SPACE`; `OPEN_WINGSUIT / RPADUP / E`; `LALT` belongs to `WINGSUIT_EVADE`, not `OPEN_PARACHUTE` | OVERSTATED |
| `rico_base.afsmb`: `S_EXIT_VEHICLE_PARA` ×2, `ACT_EXIT_VEHICLE` ×1; `rico_base.asb`: `PPparachute_vehicle_eject` ×1 | 127 | `Research/JC3Grab/EJECT_MAP.md:85,89,90` | `PPparachute_vehicle_eject ... 1`; `S_EXIT_VEHICLE_PARA ... 2`; `ACT_EXIT_VEHICLE ... 1` | VERIFIED |
| `FIRE_VEHICLE_WEAPON_PRIMARY` = `RSHOULDER`/`MOUSE1` | 128 | `Research/JC3Grab/INPUT.md:78` | Same row | VERIFIED |
| `FIRE_VEHICLE_WEAPON_SECONDARY` = `LSHOULDER`/`MOUSE2`; `VEHICLE_CAM` = `RSTICKBUTTON`/`B` | 129 | `Research/JC3Grab/INPUT.md:79,197` | Same two rows | VERIFIED |
| `QuickGadgetB` → `SelectVehicleWeapon(1)` on B at line 268 | 130 | `Research/BatmobileGrab/CONTROLS_CONSUMERS.md:28,257` | `QuickGadgetB script = VCALL SelectVehicleWeapon with a 1-valued argument`; B @268 | VERIFIED |
| `QuickGadgetX` → `SelectVehicleWeapon(2)` on X at line 269 | 131 | `Research/BatmobileGrab/CONTROLS_CONSUMERS.md:65,258` | `X_QuickGadgetX_arg ... value 2`; X @269 | VERIFIED |
| `QuickGadgetY` → `SelectVehicleWeapon(3)` on Y at line 270 | 132 | `Research/BatmobileGrab/CONTROLS_CONSUMERS.md:66,259` | `Y_QuickGadgetY_arg ... value 3`; Y @270 | VERIFIED |
| `SelectVehicleWeapon 4` is on D-pad Up at line 259 | 133 | `Research/BatmobileGrab/CONTROLS.md:55` | `SelectVehicleWeapon ... :259 XboxTypeS_DPad_Up` | VERIFIED |
| The 4th pointer is `mounted_weapon` / `id:AC0BC788` | 133 | `Research/JC3Grab/WEAPON_WIRING.md:13–14` | `mounted_weapon` = 1st gunner; `id:AC0BC788` = `mounted_weapon_2` = 2nd gunner | OVERSTATED |
| `PursuitModeWeapons[10]` is BmAK's own array | 133 | `Research/BatmobileGrab/OFFSETS.md:406–407` names the property; `Research/BatmobileGrab/BMSDK_OFFSETS.json` would settle its length | Property `PursuitModeWeapons` exists at two offsets; no source states a 10-element array | UNKNOWN |
| Sonar: `BatmobileSonar` on L3 at line 256 | 134 | `Research/BatmobileGrab/CONTROLS.md:48`; `Research/BatmobileGrab/CONTROLS_CONSUMERS.md:245` | `BatmobileSonarPressed ... XboxTypeS_LeftThumbstick ... :256` | VERIFIED |
| `BmGame.BML_Sonar` is 355,830 B with 6 verified events | 134 | `tmp/freebuff/reports/apply-gadget-rows.md:14` | `BML_Sonar bank (355,830 B, 7 HIRC / 6 verified events)` | VERIFIED |
| Enter: shipped table `RPADUP`, export `Y`, 0 face buttons shipped | 135, 144–146 | `Research/JC3Grab/EJECT_MAP.md:54,69` | `ENTER_VEHICLE ... RPADUP ... Y`; `no face button (0 rows for A/B/X/Y)` | VERIFIED |
| `entry.driver` has `check` 0, `min` 0, `max` 3 | 135 | `Research/JC3Grab/INTERACTION.md:40` states only the object/state; `Research/JC3Grab/INTERACTION.json` would settle the occupancy fields | Line 40: `entry.driver / CInteractionGraphEntry / S_ENTER_DRIVER_VEHICLE`; no `check`/`min`/`max` values | UNKNOWN |
| Exit: shipped table `RPADUP`, export `Y` | 136 | `Research/JC3Grab/EJECT_MAP.md:55` | `EXIT_VEHICLE ... RPADUP ... Y` | VERIFIED |
| `LB` = `DualPlay` at line 271; `DualPlayPressed` is 17 script bytes with 0 exit calls | 43–44, 152–153, 262 | `Research/BatmobileGrab/CONTROLS_CONSUMERS.md:46–47,260` | `:271 runs DualPlay`; `DualPlayPressed is 17 bytes ... no virtual or final call to an exit function` | VERIFIED |
| `LB` is not in either JC3 table as an exit | 43 | `Research/JC3Grab/EJECT_MAP.md:113,148` | Export LSHOULDER list and shipped 8-token list contain no `EXIT`/`EJECT` | VERIFIED |
| `ExitVehicle` alias is at `DefaultInput.ini:178` and is referenced by 0 key lines | 147 | `Research/BatmobileGrab/CONTROLS.md:95` | `ExitVehicle / ...:178 ... / none` | VERIFIED |
| `ExitVehiclePressed` is absent from `BmGame.upk`'s name table | 136, 154 | `Research/BatmobileGrab/CONTROLS.md:308` | `ExitVehiclePressed / False / 0` | VERIFIED |
| `CONTROLS.md` has 30 vehicle rows, none an enter | 146 | `Research/BatmobileGrab/CONTROLS.md:47–76` | 30 table rows (counted), no enter token | VERIFIED |
| Player export `kepmap.txt` has 249 rows and puts enter and exit both on `Y` | 145 | `Research/JC3Grab/EJECT_MAP.md:17,54–55` | `249 rows`; both export values `Y` | VERIFIED |
| Entry is covered by a 0.433 s **entry clip** | 261 | `Research/BatmobileGrab/ANIMATIONS.md:88`; `tmp/freebuff/reports/entry-exit-and-controls-plan.md:285` | `0.433 s` is `Cockpit_Open` (14 frames, 23 tracks, bone `canopy`), not an entry clip | OVERSTATED |
| Eject→glide lead is 3.7333 s | 267 | `Research/BatmobileGrab/EJECT_MOVE.md:25` | `duration 3.7333 s (113 frames @ 30 fps)` | VERIFIED |
| 8 slots across 4 `CCar` roots (`main_weapon` + `id:00568A74`) | 32, 169, 216 | `tmp/freebuff/reports/apply-weapon-slot-rows.md:26–27` | `Four CCar roots ... each with main_weapon ... and id:00568A74 non-null = 8 slots` | VERIFIED |
| Four engine-named actions: primary, secondary, `USE_VEHICLE_MOD`, `USE_ITEM` | 32, 169–170 | `Research/JC3Grab/INPUT.md:78–79,195–196` | All four present | VERIFIED |
| `SelectVehicleWeapon` handler is export 105040, 10 script bytes; gate chain is export 104971 | 168 | `Research/BatmobileGrab/CONTROLS_CONSUMERS.md:100,123` | 105040 = `QuickGadgetX`, 10 script bytes; 104971 = `SelectVehicleWeapon`, 448 script bytes | OVERSTATED |
| `ACT_EJECT_FROM_VEHICLE` at `0x23d4528`, `_MG` at `0x23d4540`, 0 refs; `ACT_EXIT_VEHICLE` in 3 files | 175–176 | `tmp/freebuff/reports/review-JC3-EJECT.md:103–104,144–150` | Same offsets; `.afsmb 0 distinct files 0`; `ACT_EXIT_VEHICLE ... .afsmb 3 distinct files 3` | VERIFIED |
| `ui/hud.gfx` is not a build target: native caller, 0 movie call sites | 232 | `Research/JC3Grab/JC3_HUD_WEAPONS.md:202–204,209` | `InitVehicleWeapons ... 2 ... TestConstructor`; `UpdateVehicleWeapons 0`; `UpdateWeaponReticle 0`; not 0 for the API as a whole | OVERSTATED |
| 2-slot display limit leaves six of the eight slots undrawn | 234 | `Research/JC3Grab/JC3_HUD_WEAPONS.md:56`; `tmp/freebuff/reports/apply-weapon-slot-rows.md:26–27` | 2 HUD slots vs 8 entity slots = 6 (arithmetic) | VERIFIED |
| Mod `.stringlookup` copy is 2,210 B, byte-identical to base; patch 2,226 B differs only in padding | 180–181 | `Research/JC3Grab/NAMES.md:86` | `2210 B, byte-identical to the base copy`; `patch copy is 2226 B and differs only in padding` | VERIFIED |
| Drop tree already ships `settings/spawn_vehicle_defs.bin` from `bm-RC4-rebel` (DROP_SRC) | 203–204 | `Tools/scripts/bm_rc4.py:69–72` | `"settings/spawn_vehicle_defs.bin": "bm-RC4-rebel"` | VERIFIED |
| `CONTROLS.md` parses 374 bindings | 276 | `Research/BatmobileGrab/CONTROLS.md:20` | `Bindings parsed: 374` | VERIFIED |
| `Working/Q/PILOT/CONTROLS.md` has a 24-row master table and conflicts A–H | 302 | `Working/Q/PILOT/CONTROLS.md:28–51,64–128` | 24 numbered rows; conflicts A–F plus G and H | VERIFIED |
| `EJECT_MAP.md` runs 24 checks | 288 | `Research/JC3Grab/EJECT_MAP.md:167` | `24/24 checks pass` | VERIFIED |
| The keymap check reproduces "145/104 **base** rows" | 247 | `Research/JC3Grab/INPUT.md:13–16,25,27` | 145/104 are the **patch** counts; base is 131/94 | OVERSTATED |

## UNKNOWN rows — the file that would settle each

1. **`HandbrakeTurnType` `0x170a`** (plan line 125). No decoded file in `Research/` or
   `Working/` states this member or offset. The earlier `entry-exit-and-controls-plan.md:232`
   lists it among `custom_land_global` members, which is a restatement, not a decode.
   Settling file: `Research/JC3Grab/VOCABULARY.md` (52 module types × 1,421 member paths)
   or the `land_global` appendix in `Research/JC3Grab/DRIVE_CARRIERS.md` §9, read against
   the Batmobile's own `…_custom_land_global.vmodc`.

2. **`PursuitModeWeapons[10]`** (plan line 133). `Research/BatmobileGrab/OFFSETS.md:406–407`
   proves the property exists (two offsets), but no file states an array length of 10.
   Settling file: `Research/BatmobileGrab/BMSDK_OFFSETS.json` / the SDK class dump behind
   `OFFSETS.md`, or the `BmGame.upk` class default for `RVehicleBatmobileBase`.

3. **`entry.driver` occupancy fields `check` 0 / `min` 0 / `max` 3** (plan line 135).
   `Research/JC3Grab/INTERACTION.md:40` names the object and its state only. The numbers
   appear in `tmp/freebuff/reports/entry-exit-and-controls-plan.md:263`, which cites
   `INTERACTION.md` line 40 — a citation that does not carry them. Settling file:
   `Research/JC3Grab/INTERACTION.json` (the decoded `entry.driver` object).

## Where the plan and its cited files disagree

- **Token count on `X`.** The plan uses "`X` and `LSHOULDER` each carry 8" to justify
  stacking three actions on one key. `LSHOULDER` 8 is verified (`EJECT_MAP.md:148`);
  `X` 8 is not in that file, and the shipped pad has no X row at all (`EJECT_MAP.md:69`).
  The same sentence appears in `entry-exit-and-controls-plan.md:419`, so the figure has
  propagated between plans without a decoded source.
- **Steering stick.** BmAK's menu says "left stick = Steer" (`CONTROLS_MENU_SCREENS.md:17`),
  but the ini line the plan cites for `aTurn`, 265, is `XboxTypeS_RightX`
  (`CONTROLS.md:69`). `aStrafe` at 263 is the left stick. The row blends the menu label
  with the ini lines.
- **Drift member count.** The plan says 21; the cited C8 source says 20
  (`DRIVE_CARRIERS.md:111`). A later plan (`air-control-closest-system-plan.md:24`) says
  21 "in the car's own module", so the two reports disagree; the cited source is 20.
- **`0.433 s` is the canopy, not entry.** `ANIMATIONS.md:88` and
  `entry-exit-and-controls-plan.md:285` both assign 0.433 s to `Cockpit_Open`
  (14 frames, 23 tracks, `canopy` bone). The pilot sentence at plan line 261 uses it as
  the seating time.
- **Export ids 105040 / 104971.** 105040 is `QuickGadgetX` (10 script bytes), the caller;
  104971 is `SelectVehicleWeapon` (448 script bytes), the body the plan calls the gate
  chain. The numbers are right, the labels are swapped (`CONTROLS_CONSUMERS.md:100,123`).
- **`hud.gfx` call sites.** `InitVehicleWeapons` has 2 call sites in `TestConstructor`
  (`JC3_HUD_WEAPONS.md:202`); only `UpdateVehicleWeapons` and `UpdateWeaponReticle` have 0.
  "0 movie call sites" is true for the update path, not the API.
- **"145/104 base rows".** 145 and 104 are the patch-layer binding counts; the base copies
  are 131 and 94 (`INPUT.md:13–16`). The offline check's numbers are right, its label is not.
- **Glide keys.** `OPEN_PARACHUTE` is `RPADDOWN`/`SPACE`, not `RPADUP`/`E`
  (`INPUT.md:156`); `LALT` is `WINGSUIT_EVADE` (`INPUT.md:202`). Only `OPEN_WINGSUIT` is
  `RPADUP`/`E`.
- **"Only `LB` collides".** `EJECT_MAP.md` §5 records B, RB, LT, LS press and X as
  displaced or conflicting JC3 controls. The narrower claim that holds is "the only
  BmAK *face* button that is an addition" — the shipped pad has no face rows at all.

## What was checked, and what was not

Checked: all 80 rows above against the cited files, read in place; byte sizes, offsets,
hashes and binding counts against `INPUT.md`; controller tokens and ini line numbers
against `CONTROLS.md`, `CONTROLS_CONSUMERS.md` and `bmak-control-scheme-storage.md`;
slot/HUD/prompt/EMP figures against their generators' reports; the existence of every
tool and build path the plan names (`Tools/scripts/{jc3_input,jc3strings_write,bm_rc4,
bm_entity,bm_leaf,eetoc}.py`; `Builds/bm-RC4-entity`; `DROP_SRC`).

Not checked / not done: the plan was not edited; no keymap, `.epe`, module, `.stringlookup`,
receipt or ledger row was written; no game install, GOG folder or save file was opened;
no game was launched. The three UNKNOWN rows cannot be closed from the files cited by the
plan — they need the settling files named above. Runtime pass bands in plan §5 (0.2 s, 3/3,
1.6–2.4 ratio) are test criteria, not data figures, and were not audited as facts.
