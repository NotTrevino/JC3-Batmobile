# Controls, entry, exit and eject — plans v2 (button by button)

Card: controls-entry-exit-eject-plans-v2. 2026-11-08. Supersedes the *numbers* of
`control-scheme-closest-system-plan.md` (315 lines) and the control half of
`entry-exit-and-controls-plan.md`; the operator rules in both are carried, not reopened.

Inputs applied in full:

| input | what it changed here |
|---|---|
| `tmp/freebuff/reports/audit-control-scheme-plan.md` | 80 figures audited — 67 VERIFIED, 9 OVERSTATED, 1 UNSUPPORTED, 3 UNKNOWN. §2 lists every one and the line that replaces it. |
| `tmp/freebuff/reports/eject-md-json-crosscheck.md` | 4 headline counts MATCHING (4,832 exits / 232 graphs / 61 names / donor 26); 3 non-headline differences recorded. |
| `tmp/freebuff/reports/eject-steps-recount.md` | donor vocabulary is **26** names, not 61; donor `exit.driver.*` exits are **8**, not 7; 15 of 17 plan figures reproduce. |
| `tmp/freebuff/reports/entry-exit-and-controls-plan.md` | the entry/exit sequence, the 12 `GetIn*` / 5 `GetOut*` members, canopy clips — cited where a row needs it, numbers corrected by the audit. |
| `tmp/freebuff/reports/gadget-wheel-input-plan.md` | BmAK selects by **index, not cycle** (`SelectVehicleWeapon 1/2/3/4`); JC3 has **no** vehicle weapon-select action. |
| `Research/BatmobileGrab/CONTROLS_MENU_SCREENS.md` | the drawn labels (pursuit + battle) and the operator decisions block at its foot. |

Labels: **decoded** = read from the cited file at the cited line; **derived** = arithmetic or
mapping over decoded facts with the rule stated; **UNKNOWN** = not in any cited file, and the file
that would settle it is named (§5).

---

## 1. The table, button by button

One row per controller button, in the order the pad reads. "BmAK decoded input code" is the
`DefaultInput.ini` token and line from `Research/BatmobileGrab/CONTROLS.md`; "JC3 shipped" is the
mounted `keymap_gamepad.bin` binding and "JC3 export" the player's `kepmap.txt` binding from
`Research/JC3Grab/INPUT.md` and `Research/JC3Grab/EJECT_MAP.md` §3.

| # | button | BmAK action | BmAK decoded input code | closest JC3 action | JC3 shipped → export | carrier member that can hold it | gap | build step | label |
|---:|---|---|---|---|---|---|---|---|---|
| 1 | **RT** | accelerate + primary fire (pursuit) / 60 mm cannon fire (battle) | `aThrottleAxis` axis, `:254` `XboxTypeS_RightTriggerAxis`; `bFireVehicleWeapon` byte, `:252` `XboxTypeS_RightTrigger` (`CONTROLS.md:68`, `:72`) | `ACCELERATE` + `FIRE_VEHICLE_WEAPON_PRIMARY` | `RTRIGGER` (`INPUT.md:50`) → `RTRIGGER` (`EJECT_MAP.md:60`); `RSHOULDER` (`INPUT.md:78`) → `RSHOULDER` (`EJECT_MAP.md:58`) | keymap binding row for `FIRE_VEHICLE_WEAPON_PRIMARY`; entity slot `main_weapon` = `851CAABE` (cannon `w602_mediumtank_canon`) | two BmAK jobs, one JC3 action each; a multi-action button is the shipped shape — LSHOULDER carries 8 tokens (`EJECT_MAP.md:148`) | add `RTRIGGER → FIRE_VEHICLE_WEAPON_PRIMARY` to the private keymap copy; slot 0 = battle cannon | decoded (both sides) + derived (the stacking) |
| 2 | **RB** | secondary fire (Vulcan, battle) / cycle view (pursuit) | `SecondaryFireVehicleWeapon`, `:272` `XboxTypeS_RightShoulder` (`CONTROLS.md:54`); `PursuitModeTagGun`, same line (`CONTROLS.md:53`); `ToggleDrivingCamera`, `:272` + `:186` `C` (`CONTROLS.md:57`) | `FIRE_VEHICLE_WEAPON_SECONDARY`; `VEHICLE_CAM` for the view job | `LSHOULDER` (`INPUT.md:79`) → `LSHOULDER` (`EJECT_MAP.md:59`); `RSTICKBUTTON` (`INPUT.md:197`) → `RSTICKBUTTON`/`B` | keymap binding row; entity slot `secondary` = `00568A74` (Vulcan `w603_mediumtank_mgun`) | LSHOULDER must be emptied for LB-exit, so secondary has to move to RB; the view job then clashes with `LOOK_BACK_CAM` | rebind `FIRE_VEHICLE_WEAPON_SECONDARY → RSHOULDER`; leave `VEHICLE_CAM` where it is until the press/hold row (§5 U4) is tested | decoded + derived |
| 3 | **X** | brake / reverse / power slide (pursuit); missile barrage (battle) | `BrakePressed`, `:269` `XboxTypeS_X` (`CONTROLS.md:49`); `bHandbrakeOrBrake`, `:269` (`CONTROLS.md:73`); slide = `left stick + RT + X` (`CONTROLS_MENU_SCREENS.md:19`) | `HANDBRAKE` + `REVERSE` | `RPADLEFT` (`INPUT.md:114`) → `X` (`EJECT_MAP.md:57`); `LTRIGGER` (`INPUT.md:178`) → `LTRIGGER` | keymap binding row (add `REVERSE` to `X`); `brakes.vmodc` handbrake factor; `custom_land_global.drift.*` — a **20**-member block (`DRIVE_CARRIERS.md:111`), fleet defaults 10 km/h / 5000 / 4 / 45° / 30000 | JC3 splits brake (LT) from handbrake (X); BmAK has one X for both, and the battle half of X has no action at all | add `X → REVERSE` beside `X → HANDBRAKE`; that empties LT for the battle hold (row 13) | decoded + derived |
| 4 | **Y** | afterburner (pursuit); Drone Virus (battle) | `bVehicleBoostButton` byte, `:270` `XboxTypeS_Y` (`CONTROLS.md:76`) | `USE_VEHICLE_MOD` (the only vehicle "ability" action) | `RPADRIGHT` (`INPUT.md:196`) → `B` (`EJECT_MAP.md:56`) | keymap binding row; `arcade.nitro_boost` (145 of 232 cars, `INPUT.md:234`); `WINGSUIT_TAKEOFF` already sits on export `Y` (`EJECT_MAP.md:67`) | no `BOOST`/`NITRO` action name exists — the only match in 154 actions is `WINGSUIT_BOOST` (`INPUT.md:274`); JC3 export Y already carries `ENTER_VEHICLE`/`EXIT_VEHICLE`/`OPEN_WINGSUIT`/`USE_ITEM` (`EJECT_MAP.md:114`) | rebind `USE_VEHICLE_MOD → Y`; keep `ENTER_VEHICLE` on Y (inert while seated, §3) | decoded + derived |
| 5 | **LB** | exit Batmobile | **no exit token**: `DualPlay` alias `:179` → binding `:271` `XboxTypeS_LeftShoulder` (`CONTROLS.md:94`), `DualPlayPressed` → `RPlayerController.SpecialMove.DualPlayPressed` (`CONTROLS.md:297`); `ExitVehicle` alias `:178` is referenced by **0** key lines; `ExitVehiclePressed` is absent from `BmGame.upk`'s name table | `EXIT_VEHICLE` | `RPADUP` (`INPUT.md:74`) → `Y` (`EJECT_MAP.md:55`) | keymap binding row **+** the `.epe` exit graph: `exit.driver.default` → `S_EXIT_VEHICLE` (161 of 4,832 exits), `exit.driver.moving.parachute` → `S_EXIT_VEHICLE_PARA` (221 exits, only gate `(5.0, 999.0)`, `EJECT_MAP.md:149–150`) | JC3 puts enter *and* exit on one control (`INPUT.md:73–74`), and the shipped pad has **0** face-button rows (`EJECT_MAP.md:69`), so the pair must be split before LB can exist; the post-exit car motion the operator specifies (pursuit: break right; battle: break straight) is authored by **no** decoded JC3 member | split the pair in the private keymap copy: `LSHOULDER → EXIT_VEHICLE` only, `Y → ENTER_VEHICLE` only; `LSHOULDER` loses `FIRE_VEHICLE_WEAPON_SECONDARY` (row 2) | decoded (split) + UNKNOWN (car motion, §5 U1) |
| 6 | **A** | eject — *double press* (menu row "Eject Into Glide") | `EjectFromVehicle`, `:267` `XboxTypeS_A` (`CONTROLS.md:50`), resolves to `RPlayerController.DrivingMode.EjectFromVehicle` (`CONTROLS.md:301`) | no `EJECT` action exists (0 matches in all four tables, `EJECT_MAP.md:147`); nearest is the speed-gated **exit** that lands in `S_EXIT_VEHICLE_PARA`; the on-foot counterpart is `OPEN_PARACHUTE` (HOLD A) | export `A` = `STUNT_JUMP` (`EJECT_MAP.md:51`) + `OPEN_PARACHUTE` (`:52`); shipped = `RPADDOWN` (`INPUT.md:156`, `:187`) | `.epe` exit graph (`exit.driver.moving.parachute`, gate `(5.0, 999.0)`); no exit carries a launch/impulse member — **0 of 4,832** do, and the only module-side member is `TrainGlobal.crashing_impulse` ×12 (`EJECT_MAP.md` §launch; `EJECT.md:188–191`) | **press count**: 0 hold/duration/tap words in 145 gamepad + 104 keyboard + 249 export rows (`EJECT_MAP.md:76`); BmAK's own double-press timer is not decoded either | bind `A → EXIT_VEHICLE` **as a second binding** in the private copy so a moving car ejects into `S_EXIT_VEHICLE_PARA` and a stopped one does a standing exit; the double-press pattern itself stays UNKNOWN | derived (binding) + UNKNOWN (press count, §5 U2) |
| 7 | **L3** | sonar / scan | `BatmobileSonarPressed`, `:256` `XboxTypeS_LeftThumbstick` (`CONTROLS.md:48`, `:214`; alias `:184`, `:86`) | none — no `SONAR`/`SCAN` action in the 154 names | shipped `LSTICKBUTTON` is in the used-control list (`EJECT_MAP.md:69`); no action owns it | `RBatmobileSonar` class + `BmGame.BML_Sonar` bank (355,830 B, 6 verified events) | no action name to bind | probe: one spare action id on `LSTICKBUTTON`, press in-car, watch for a scan pass | UNKNOWN (§5 U3) |
| 8 | **D-pad Up** | weapon slot 4 (missile pods) | `SelectVehicleWeapon 4` / `OnRelease ReleaseVehicleWeapon 4`, `:259` `XboxTypeS_DPad_Up` (`CONTROLS.md:55`) | `USE_ITEM` (the only D-pad Up vehicle action) | `RPADUP` (`INPUT.md:195`); export binding not in `EJECT_MAP.md` §3 — UNKNOWN | keymap binding row; entity slots `mounted_weapon` / `id:AC0BC788` (both ship null, `WEAPON_WIRING.md:13–14`) | `USE_ITEM` is already consumed by the EMP path (`trigger.use_item` → `S_STUNT_USE_ITEM_VEHICLE`, `EMP.md:80–82`), so slot 4 and EMP claim the same action | keep `RPADUP → USE_ITEM`; give the missile pod one of the two null entity slots | decoded + UNKNOWN (export row) |
| 9 | **D-pad Right** | **power winch** (operator decision; replaces Mission Select) | **no BmAK token** — 0 hits for `winch`/`tether` in `CONTROLS.md`, `CONTROLS_CONSUMERS.md`, `BINDINGS_MERGED.md`; `RBatmobileWinch` is a class, never a binding | `VEHICLE_RELEASE_GRAPPLE` (+ `FIRE_GRAPPLE` for the attach half) | `LPADDOWN` (`INPUT.md:198`), `MOUSE2`/`LSHOULDER` (`INPUT.md:75`); shipped `RPADRIGHT` currently belongs to `USE_VEHICLE_MOD` (`INPUT.md:196`) | keymap binding row; donor tether mechanic | `USE_VEHICLE_MOD` must leave RPADRIGHT (its export key is `B`, `EJECT_MAP.md:56`), and the grapple pair is on two other buttons today | rebind `RPADRIGHT → FIRE_GRAPPLE` (attach) and keep `VEHICLE_RELEASE_GRAPPLE` as the release half | derived (operator rule + decoded actions) |
| 10 | **B** | quick gadget 1 — Tracker / Immobilizer (pursuit), EMP (battle) | `QuickGadgetB`, `:268` (`CONTROLS.md:386`) → `SelectVehicleWeapon(1)` (`CONTROLS_CONSUMERS.md:28`, `:257`) | no vehicle weapon-select action exists (gadget plan §5) | export `B` = `USE_VEHICLE_MOD` (`EJECT_MAP.md:56`) — displaced, recorded at `EJECT_MAP.md:115` | keymap binding row; `SelectVehicleWeapon` script export | JC3's two slots are fired by two buttons and selected by none; the 10-byte handler (`QuickGadgetX` = export **105040**) only *calls* `SelectVehicleWeapon` (export **104971**, 448 bytes) — the old plan had those two ids labelled the wrong way round | rebind `B` to the slot-select action once a keymap writer exists (§4) | decoded + derived |
| 11 | **X (battle role)** | quick gadget 2 — Missile Barrage | `QuickGadgetX`, `:269` (`CONTROLS.md:387`) → `SelectVehicleWeapon(2)` (`CONTROLS_CONSUMERS.md:65`, `:258`) | as row 10 | as row 10 | as row 10 | X's two BmAK jobs (row 3 vs this row) are separated by mode only; JC3 has no mode-scoped keymap | same rebind as row 10; the mode split is the mode card's | decoded |
| 12 | **Y (battle role)** | quick gadget 3 — Drone Virus | `QuickGadgetY`, `:270` (`CONTROLS.md:388`; note it resolves inside `RPlayerController.CinematicMode`, a decoded quirk) → `SelectVehicleWeapon(3)` (`CONTROLS_CONSUMERS.md:66`, `:259`) | as row 10 | as row 10 | as row 10 | as row 10 | same rebind as row 10 | decoded |
| 13 | **LT** | hold = Battle Mode, release = Pursuit | `aLeftTrigger` axis, `:253` `XboxTypeS_LeftTriggerAxis` (`CONTROLS.md:60`) | `REVERSE` is what ships on LT | `LTRIGGER` (`INPUT.md:178`); owner table records LT displacing `REVERSE` (`EJECT_MAP.md:119`) | keymap binding row; mode members are the mode card's | LT is BmAK's mode hold and JC3's reverse; reverse has to move to X first (row 3) | none here beyond row 3's rebuild; the threshold numbers belong to the mode-switch card | decoded |
| 14 | **LS / left stick** | steer (+ move in battle) | `aStrafe` axis, `:263` `XboxTypeS_LeftX` (`CONTROLS.md:67`); `aBaseY`, `:264`; menu says "left stick = Steer" (`CONTROLS_MENU_SCREENS.md:17`) | `TURN_LEFT` / `TURN_RIGHT` — no plain land row located; only `HELI_TURN_LEFT` `RSTICKLEFT` (`INPUT.md:121`) and `PLANE_TURN_LEFT` `RPADLEFT` (`:164`) | — | keymap binding rows; `land_steering.vmodc` (`steer_angle_*`, `steering_type`) | **audit OVERSTATED row**: the old plan put steering on LS at lines 263/265, but 265 is `RightX` — the menu label and the ini axis disagree; BmAK's steering curve is also undecoded | no key change (JC3 already steers on the sticks); the number row stays open | decoded (codes) + UNKNOWN (curve, §5 U6) |
| 15 | **RS / right stick** | look around; press = look behind (pursuit) / zoom (battle) | `bLookBehindVehicle`, `:255`; menu rows `right stick` / `right stick press` (`CONTROLS_MENU_SCREENS.md:21–22`) | `LOOK_BACK_CAM`, `VEHICLE_CAM`, `PRECISION_AIM` — three actions on one button | all three on `RSTICKBUTTON` (`INPUT.md:128`, `:197`) | keymap binding rows | press vs hold has no field in any table (`EJECT_MAP.md:76`) | leave as shipped; one tap-vs-hold probe (§5 U4) decides whether `VEHICLE_CAM` needs moving | decoded (codes) + UNKNOWN (press/hold) |
| 16 | **Start** | pause | `UserPause`, `:262` (`CONTROLS.md:493`) | `GUI_PAUSE` | `START` (`INPUT.md:99`) → `START` (`EJECT_MAP.md:65`) | keymap binding row — untouched | none: operator rule keeps JC3's pause | nothing | decoded |
| 17 | **Back / View** | WayneTech menu | `OpenLevelUpOrMap`, `:261` (`CONTROLS.md:363`) | `GUI_PDA` (commlink) | `BACK` (`INPUT.md:100`) → `BACK` (`EJECT_MAP.md:66`) | keymap binding row — untouched | BmAK's map row loses by operator rule | nothing | decoded |
| 18 | **(outside the car) enter** | none — BmAK has **no** enter binding at all | no token: the 30-row vehicle action table has no enter row, and `ExitVehicle`'s neighbour alias is unbound | `ENTER_VEHICLE` | `RPADUP` (`INPUT.md:73`) → **`Y`** (`EJECT_MAP.md:54`) | `.epe` `entry.driver` (`CInteractionGraphEntry` → `S_ENTER_DRIVER_VEHICLE`, `INTERACTION.md:40`) + keymap binding row | the shipped pad binds no face button (`EJECT_MAP.md:69`), so Y-enter is a **new** binding, not a move; the entry occupancy numbers are undecoded | add `Y → ENTER_VEHICLE` in the patch-layer gamepad keymap (patch = 145 bindings, 7,207 B, entry offset 610,914,304, sha256 `0944e37d8588feed`, `INPUT.md:14`) | decoded (absence) + derived (binding) |

**One correction to the old priority sentence.** "The only BmAK button that collides with a JC3
token is LB" is **OVERSTATED** (`audit-control-scheme-plan.md`, the 9-overstated group): the owner
table records B displacing `USE_VEHICLE_MOD`, RB displacing primary fire, LT displacing `REVERSE`,
LS press displacing the horn, and X colliding with `HANDBRAKE` (`EJECT_MAP.md:112–121`). The claim
that survives is narrower and is the one this table uses: **BmAK's face buttons are additions, not
displacements, because the shipped pad binds no face button at all** (`EJECT_MAP.md:69`).

---

## 2. Every audit correction applied

The audit's verdicts, and what each becomes in this table. Nothing below is a re-reading of the
audit — each row cites the file the audit tested.

| # | old claim (plan line) | verdict | corrected value, and where it comes from |
|---:|---|---|---|
| C1 | `X` and `LSHOULDER` "each carry 8 tokens" (29, 75) | **UNSUPPORTED** | `LSHOULDER` 8 is real (`EJECT_MAP.md:148`); **no X count exists** — the shipped pad has no X row at all (`:69`), and export X carries **3** (`FIRE_WINGSUIT_WEAPON_SECONDARY`, `HANDBRAKE`, `RELOAD`, `:116`). Row 3 uses the export-3 fact only. |
| C2 | "the only colliding button is LB" (24–26) | **OVERSTATED** | five collisions, listed at `EJECT_MAP.md:112–121` (see the note above). |
| C3 | steering `aTurn`/`aStrafe` on LS, lines 263/265 (122) | **OVERSTATED** | `aStrafe` `:263` = `LeftX` (`CONTROLS.md:67`); **`aTurn` `:265` = `RightX`** (`CONTROLS.md:69`). Row 14 states the disagreement with the menu label instead of blending them. |
| C4 | `CustomLandGlobal.drift.*` has 21 members (125) | **OVERSTATED** | **20** members on 145 builds (`DRIVE_CARRIERS.md:111`). Row 3. |
| C5 | glide keys `OPEN_PARACHUTE`/`OPEN_WINGSUIT` = `RPADUP`/`E`, `LALT` (127) | **OVERSTATED** | `OPEN_PARACHUTE` = `RPADDOWN`/`SPACE` (`INPUT.md:156`); `OPEN_WINGSUIT` = `RPADUP`/`E` (`:157`); `LALT` belongs to `WINGSUIT_EVADE` (`:202`). Row 6 uses the export pair (`A` + HOLD A). |
| C6 | 4th slot pointer = `mounted_weapon` / `id:AC0BC788` (133) | **OVERSTATED** | `mounted_weapon` is the **1st gunner** and `id:AC0BC788` is `mounted_weapon_2` — different pointers (`WEAPON_WIRING.md:13–14`). Row 8 lists both as distinct null slots. |
| C7 | `SelectVehicleWeapon` handler = export 105040; gate chain = 104971 (168) | **OVERSTATED** | **105040 is `QuickGadgetX`** (10 script bytes); **104971 is `SelectVehicleWeapon`** (448 bytes) (`CONTROLS_CONSUMERS.md:100`, `:123`). Row 10. |
| C8 | `hud.gfx` "0 movie call sites" (232) | **OVERSTATED** | 0 is true for `UpdateVehicleWeapons` / `UpdateWeaponReticle`; `InitVehicleWeapons` has **2** call sites in `TestConstructor` (`JC3_HUD_WEAPONS.md:202–204`). Not a control row — recorded because the same sentence appears in two plans. |
| C9 | keymap check reproduces "145/104 **base** rows" (247) | **OVERSTATED** | 145/104 are the **patch** counts; base is **131/94** (`INPUT.md:13–16`). Row 18 and §4 cite patch only. |
| C10 | entry is covered by a 0.433 s entry clip (261) | **OVERSTATED** | 0.433 s is `Cockpit_Open` (14 frames, 23 tracks, bone `canopy`), not an entry clip (`ANIMATIONS.md:88`). No entry-timing number is used in this table. |
| C11 | `HandbrakeTurnType` = `0x170a` (125) | **UNKNOWN** | no decoded file states the offset; the old plan only restates the earlier one. Settler: `Research/JC3Grab/VOCABULARY.md` or the `land_global` appendix in `DRIVE_CARRIERS.md` §9. Row 3 keeps the member unnamed. |
| C12 | `PursuitModeWeapons[10]` (133) | **UNKNOWN** | `OFFSETS.md:406–407` proves the property, no file states a length of 10. Settler: `Research/BatmobileGrab/BMSDK_OFFSETS.json` or the `BmGame.upk` class default. Row 8 does not quote a length. |
| C13 | `entry.driver` occupancy `check` 0 / `min` 0 / `max` 3 (135) | **UNKNOWN** | `INTERACTION.md:40` names the object and state only. Settler: `Research/JC3Grab/INTERACTION.json`. Row 18 says the numbers are undecoded. |

Verified rows worth stating because this table depends on them: patch gamepad keymap 145 bindings /
7,207 B / offset 610,914,304 / sha256 `0944e37d8588feed` (`INPUT.md:14`); 12 B per binding, 18 B of
property records, both properties `stringZ` (`INPUT.md:20`, `:25`, `:29`); 16 land-vehicle action
names (`INPUT.md:223`); `ENTER_VEHICLE` and `EXIT_VEHICLE` share `RPADUP` (`INPUT.md:73–74`).

---

## 3. What the operator rules fix, and what they cost

Restated as constraints only — not reopened (`CONTROLS_MENU_SCREENS.md`, operator block at its foot;
`CONTROLS_MENU_SCREENS.md:17`, `:19`, `:20`, `:22`):

1. **Inside the car, BmAK wins except pause and commlink.** Rows 16–17 implement that with no edit.
2. **Enter = JC3's Y.** Row 18: a *new* binding (the shipped pad has no face rows), cheap because
   nothing is displaced.
3. **Exit = LB.** Row 5: the only structural edit in the whole scheme — JC3's enter/exit pair must
   be split, which is a keymap data edit, not a new system.
4. **Eject = double press of A, with hold-A parachute as its JC3 counterpart.** Row 6: the exit
   half is data (a speed-gated exit already lands in `S_EXIT_VEHICLE_PARA`); the *double press* is
   the one thing no decoded table can express (§5 U2).
5. **Winch = D-pad Right.** Row 9: BmAK never bound a winch, and `RPADRIGHT` currently carries
   `USE_VEHICLE_MOD` for JC3 — so the rule costs one displaced mod binding, which row 4 re-homes to Y.

**Two consequences the operator rules do not state but the tables force** (derived, flagged):

* **Y is inert inside the car by intent, not precedence.** Because the keymap is global — 0 of 232
  entity dumps name a keymap, 0 of 134 vehicle modules name an action (`INPUT_D11.md:5`, `:70`,
  `:72`) — `ENTER_VEHICLE` on Y cannot be suppressed per-entity. It simply has no enter prompt to
  consume while seated, which is what makes Y available for the afterburner.
* **RT does both.** `ACCELERATE` and primary fire share RT, so in battle the cannon fires on the
  same press that accelerates. This is BmAK's own shape (RT = accelerate in pursuit, 60mm Cannon in
  battle, `CONTROLS_MENU_SCREENS.md:9`, `:36`) and JC3 tolerates it — a multi-action key is the
  shipped shape (`EJECT_MAP.md:148`).

---

## 4. The blocker: no keymap writer exists

Every keymap row above (1, 2, 3, 4, 5, 6, 8, 9, 10, 18) ends in the same build step: edit a binding
row in a keymap bin. Checked, decoded:

| check | result |
|---|---|
| scripts that read `keymap_gamepad` | `jc3_input.py`, `jc3_eject_map.py`, `jc3_drive_carriers.py`, `reset_status*.py` — all censuses |
| a keymap **writer** in `Tools/scripts` (575 files) | **none**: `jc3_input.py` header says "Read-only. Writes (with `--write`) or re-derives and compares", and its `build()` emits `INPUT.json`, not a bin |
| does the mod ship a keymap today | **no** — the drop manifest carries one `settings/` entry, `settings/spawn_vehicle_defs.bin` (`Tools/scripts/bm_rc4.py:71`) |

So the first build step in any of these rows is not the binding, it is **the writer**: serialise the
12-byte binding record + its 18 B of `stringZ` property records (`INPUT.md:20`, `:25`) into the
patch-layer gamepad file (7,207 B at offset 610,914,304) and confirm the result re-parses to 145
bindings with the same tail-0 tiling (`INPUT.md:25`). Until that exists, a row that says "rebind"
is a plan, not a build.

---

## 5. UNKNOWNs — the file that settles each, and one passing check

| # | UNKNOWN | row(s) | settles with | one pilot check, with band |
|---:|---|---|---|---|
| U1 | the car's post-exit motion: pursuit exit → car breaks right, battle exit → car breaks straight | 5 | no decoded JC3 member authors it; the BmAK side is the `GetOut*` body plus `EJECT_VELOCITY.md` (velocity `(0,0,0)` written on `Car.Mesh` at +513 for eject only) | Exit at speed in each mode 3×; record the car's heading change over the first second. Pursuit: car yaws right 3/3; battle: straight within ±5° 3/3. |
| U2 | the **double press** that turns A into Eject Into Glide | 6 | `Research/JC3Grab/INPUT.md` — no hold/duration/tap field in 145+104+249 rows (`EJECT_MAP.md:76`); would live in native input code or a table not in the index (`EJECT_MAP.md:129`). BmAK's own timer is likewise undecoded | Press A once, then twice, from a moving car. Single press: standing/moving exit 3/3. Double: `S_EXIT_VEHICLE_PARA` 3/3 and 0 crashes. |
| U3 | the sonar trigger (no `SONAR`/`SCAN` action exists) | 7 | a keymap probe on `LSTICKBUTTON` with a spare action id; action census is `INPUT.md` | Press L3 with a target 20 m behind a wall. Scan visual 3/3, or 0/3 and the row is re-queued — no silent pass. |
| U4 | press vs hold on `RSTICKBUTTON` (`VEHICLE_CAM` + `LOOK_BACK_CAM`) and whether a patched dropzone keymap is honoured at all | 2, 15 | `INPUT.md` §UNKNOWN (no hold field anywhere); the dropzone probe named in `Working/Q/PILOT/CONTROLS.md` §2-G | Tap R3 (view cycles 5/5); hold R3 1 s (camera swings back 5/5 and releases 5/5). |
| U5 | `PursuitModeWeapons[10]` length | 8 | `Research/BatmobileGrab/BMSDK_OFFSETS.json` / the `BmGame.upk` class default | — (data read, no pilot needed) |
| U6 | BmAK's steering response curve (`aTurn` has no decoded curve) | 14 | `RVehicleSimBatmobile.StandardSteeringSpeedCurve` / `DesiredTurnOnSpotSpeed` are the read sites; values need the capture set | Full lock at 30 and 120 km/h; ratio of times to 90° heading change inside 1.6–2.4. |
| U7 | `HandbrakeTurnType` offset | 3 | `Research/JC3Grab/VOCABULARY.md` or `DRIVE_CARRIERS.md` §9 against the car's own `.vmodc` | — (data read) |
| U8 | `entry.driver` occupancy fields (`check`/`min`/`max`) | 18 | `Research/JC3Grab/INTERACTION.json` | — (data read) |

**Eject's data side is not an UNKNOWN.** Cross-checked: `EJECT.md` and `EJECT.json` agree on all
four headline counts — 4,832 exits, 232 graphs, 61 names, donor 26 (`eject-md-json-crosscheck.md`
§headline table), and the recount reproduces 15 of 17 plan figures. Two corrections matter for the
eject row:

* "the donor's 61-name vocabulary" → the donor has **26** names; 61 is the fleet vocabulary
  (`eject-steps-recount.md` row 2).
* "the donor's seven driver exits all carry no modifier" → there are **eight** `exit.driver.*`
  donor exits, all null-modifier (`eject-steps-recount.md` row 14; `EJECT.json` `donor.exits`).
* `exit.driver.moving.parachute` exists on **221 of 232** vehicles (`eject-steps-recount.md` row 6),
  and every one of the 4,832 exits is `enabled=1` (`EJECT.md:27`).
* No exit carries a launch member — **0 of 4,832** — so "eject into glide" cannot come from an
  authored impulse on either side; it comes from the exit's state (`S_EXIT_VEHICLE_PARA`) and the
  parent-speed gate only.

---

## 6. Checks run for this page

| check | result |
|---|---|
| audit results applied | 13 rows (§2): 9 overstated, 1 unsupported, 3 UNKNOWN — each with the replacing line |
| every BmAK token line re-read | `CONTROLS.md:48–50, 53–57, 60, 67–69, 72–73, 76, 86, 94, 297, 301, 363, 386–388, 493` |
| every JC3 binding re-read | `INPUT.md:50, 73–79, 99–100, 114, 128, 156–157, 178, 187, 195–198`; `EJECT_MAP.md:51–52, 54–55, 57, 59–60, 65–67, 69, 76, 112–123, 147–150` |
| counts re-checked | 145/104 patch vs 131/94 base; 0 face rows; 8 LSHOULDER tokens; 3 export X tokens; donor 26 names / 8 driver exits; 221 of 232; 4,832 exits |
| keymap writer claim | `grep` over 575 `Tools/scripts/*.py`: 0 writers; drop manifest has one `settings/` entry |
| files edited | **none** except this page |
| game launched / archive written | **no** |

Revert: delete this file. No plan, keymap, `.epe`, module or build was modified.
