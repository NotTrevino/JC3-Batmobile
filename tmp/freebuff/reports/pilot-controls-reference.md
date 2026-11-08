# Pilot controls reference (Q-PILOT step 3)

Canonical document: **`Working/Q/PILOT/CONTROLS.md`** (written this card). This report is the
summary a reviewer reads first; the canonical file carries the full rows, the conflict analysis
and the small-model rules.

Sources, kept apart in both files:

* **JC3 side** (what can actually be pressed in the drop): `Research/JC3Grab/INPUT.md` (G3-08,
  474 bindings / 154 actions decoded from `settings/keymap_keyboard.bin` and
  `settings/keymap_gamepad.bin`, patch layer), `Research/JC3Grab/INPUT_D11.md`.
* **BmAK side** (the Batmobile's own scheme): `BmGame/Config/DefaultInput.ini` lines via
  `Research/BatmobileGrab/CONTROLS.md`, `BINDINGS_KEYBOARD.md`, `BINDINGS_MERGED.md`, plus the
  transcribed in-game controls screen in `CONTROLS_MENU_SCREENS.md`.
* Decision: `GRAB_BACKLOG.md` D-11 — enter uses JC3's control, everything else BmAK's; inside the
  Batmobile BmAK wins, JC3's pause and commlink keep priority.

Labels: `decoded` = read from a file; `menu label` = named by BmAK's controls screen only;
`UNKNOWN` = no file binding — which includes bindings the operator stated but no file contains.

## Table (as in the canonical file)

| # | Action | Keyboard | Gamepad | What the screen shows after | Source | Label |
|---:|---|---|---|---|---|---|
| 1 | Enter | `E` (JC3 `ENTER_VEHICLE`) | `D-Pad Up` (JC3 `ENTER_VEHICLE`) | JC3 enter prompt consumed → Batmobile HUD | `INPUT.md` ENTER_VEHICLE=RPADUP/E; D-11 | decoded; operator "Y" = **UNKNOWN** (conflict A) |
| 2 | Exit | `E` (JC3 `EXIT_VEHICLE`) | `D-Pad Up`; BmAK `LB` | menu "Exit Batmobile"; Rico steps out, third person | `INPUT.md`; `CONTROLS_MENU_SCREENS.md`; `DefaultInput.ini:271` (LB=DualPlay); D-11 | E/DPad decoded; LB **UNKNOWN** (conflict B) |
| 3 | Accelerate | `W` (JC3 `ACCELERATE`) | `RT` (BmAK `aThrottleAxis`) | menu "Accelerate"; speed/gear HUD | `INPUT.md`; `DefaultInput.ini:254`; menu screen | decoded |
| 4 | Brake / reverse | `S` (JC3 `REVERSE`) | `LT` (JC3 `REVERSE`); BmAK `X` | menu "Brake / Reverse" | `INPUT.md`; `DefaultInput.ini:269` (`BrakePressed`, `bHandbrakeOrBrake`) | S/LT decoded; X **UNKNOWN** (conflict C) |
| 5 | Reverse | `S` | `LT` | car backs up | `INPUT.md` | decoded |
| 6 | Steer | `A`/`D` (`TURN_LEFT`/`TURN_RIGHT`) | left stick L/R | menu "Steer"; car yaws | `INPUT.md` | decoded |
| 7 | Handbrake / drift | `LShift` (`HANDBRAKE`) | `D-Pad Left`; BmAK `X` | menu "Power Slide" (stick+RT+X) | `INPUT.md`; `CONTROLS.md`; menu screen | LShift/DPad decoded; combo `menu label` |
| 8 | Boost / afterburner | **UNKNOWN** (no JC3 action; only `WINGSUIT_BOOST` exists) | **UNKNOWN** (BmAK `Y`, `bVehicleBoostButton`, `DefaultInput.ini:270`) | menu "Afterburner" (pursuit) / "Drone Virus" (battle) | `CONTROLS.md`; `INPUT.md` §BmAK→JC3; menu screen | BmAK decoded; JC3 **UNKNOWN** |
| 9 | Jump | n/a — BmAK cannot jump | n/a | nothing (JC3 `JUMP` is on-foot) | D-10; `INPUT.md` | absent by decision |
| 10 | 60 mm cannon | `LMB` (`FIRE_VEHICLE_WEAPON_PRIMARY`) | `RB`; BmAK `RT` | menu "60mm Cannon"; `DrawWeaponPowerLevel` | `INPUT.md`; `DefaultInput.ini:252`; `CONTROLS_CONSUMERS.md` | decoded action; BmAK slot `menu label` |
| 11 | Vulcan gun | `RMB` (`FIRE_VEHICLE_WEAPON_SECONDARY`) | `LB`; BmAK `RB` | menu "Vulcan Gun" | `INPUT.md`; `DefaultInput.ini:272`; menu screen | decoded action; slot `menu label` |
| 12 | Tracker / immobilizer | **UNKNOWN** (near-name `USE_ITEM` `E`, 0 vehicle consumers) | **UNKNOWN** (BmAK `B` → `SelectVehicleWeapon(1)`, `:268`) | menu "Tracker / Immobilizer"; brackets then missile | `CONTROLS.md`; `CONTROLS_CONSUMERS.md` §2; `INPUT_D11.md`; D-11 | **UNKNOWN** (conflict D) |
| 13 | Missile barrage | **UNKNOWN** | **UNKNOWN** (BmAK `X` → slot 2, `:269`) | menu "Missile Barrage"; `DrawWeaponSelectHud` | `CONTROLS.md` (QuickGadgetX arg 2) | **UNKNOWN** |
| 14 | Drone virus / hacker | **UNKNOWN** | **UNKNOWN** (BmAK `Y` → slot 3, `:270`) | menu "Drone Virus" | `CONTROLS.md` (QuickGadgetY arg 3) | **UNKNOWN** |
| 15 | EMP burst | **UNKNOWN** | **UNKNOWN** (BmAK `B`; menu says EMP) | menu "EMP"; blue pulse, vehicles stall | `CONTROLS_MENU_SCREENS.md` battle; D-11 | **UNKNOWN** (conflict D/E) |
| 16 | Sonar | **UNKNOWN** (no SONAR/SCAN action) | **UNKNOWN** (BmAK `L3`, `BatmobileSonar`, `:256`) | battle d-pad "Scan"; sonar pulse | `CONTROLS.md`; `INPUT.md` | **UNKNOWN** |
| 17 | Weapon 4 / missile pods | **UNKNOWN** (`NEXT_WEAPON`/`PREV_WEAPON` unproven on vehicles) | **UNKNOWN** (BmAK `D-Pad Up`, `SelectVehicleWeapon 4`, `:259`) | `DrawWeaponSelectHud` moves the highlight | `CONTROLS.md`; `INPUT.md` | **UNKNOWN** |
| 18 | Mode switch battle↔pursuit | **UNKNOWN** (0 actions match BATTLE/PURSUIT/MODE$) | **UNKNOWN** (BmAK `LT` hold/release, `aLeftTrigger`, `:253`; call path undecoded) | menu "Battle Mode"/"Pursuit Mode"; plates fold, weapons swap | `CONTROLS_MENU_SCREENS.md`; `CONTROLS_CONSUMERS.md` §1; `INPUT.md`; D-11 | **UNKNOWN** (live-confirmed, not in a file) |
| 19 | Eject into glide | **UNKNOWN** (no EJECT action) | **UNKNOWN** (BmAK `A A`, `EjectFromVehicle`+`BattleStrafe`, `:267`) | menu "Eject Into Glide"; canopy blows, Rico glides | menu screen; `CONTROLS_CONSUMERS.md` §5 | **UNKNOWN** |
| 20 | Power winch | **UNKNOWN** (`V` `VEHICLE_RELEASE_GRAPPLE` / `MMB` `USE_VEHICLE_MOD`) | **UNKNOWN** (decided `D-Pad Right`, 2026-11-05) | cable tethers the car to the target | menu screen (operator decision); `INPUT.md` | **UNKNOWN** |
| 21 | Driving camera | `B` (`VEHICLE_CAM`) | `R3`; BmAK `C`/`RB` | menu "Cycle View" | `INPUT.md`; `DefaultInput.ini:186`, `:272` | decoded |
| 22 | Look behind | `B` (`LOOK_BACK_CAM`, shares the key — conflict F) | `R3` (BmAK `bLookBehindVehicle`, `:255`) | menu "Look Behind"; camera snaps back while held | `INPUT.md`; `CONTROLS.md` | decoded |
| 23 | Pause / commlink (JC3 priority) | `Esc`, `Tab` | `Start`, `Back` | pause overlay; map/commlink | `INPUT.md` (GUI_PAUSE/GUI_PDA); operator note | decoded |
| 24 | WayneTech screen | **UNKNOWN** | **UNKNOWN** (BmAK View/back → `OpenLevelUpOrMap`, `:261`) | menu "WayneTech"; upgrade screen | `CONTROLS_MENU_SCREENS.md`; `CONTROLS.md` | **UNKNOWN** |

Weapon coverage: cannon (10), Vulcan (11), tracker+EMP missile (12), EMP burst (15), hacker (14),
sonar (16), barrage (13), missile pods / weapon 4 (17); booster mesh is the visual of row 8; riot
mode is a named omission (D-3, JC3 lethality accepted) and has no row.

## Where the reference is honest about gaps

Eight conflict/gap items are written out in `Working/Q/PILOT/CONTROLS.md` §2, each with the file
that settles it and a one-sentence pilot-card check:

A enter `Y` vs file `E`/`D-Pad Up` (also D-11's "LB = enter"); B exit `LB` vs `DualPlay`;
C brake `X` vs JC3 `LT` = reverse and battle hold; D `B` = tracker vs `B` = EMP;
E battle weapons are *selected* slots (`SelectVehicleWeapon 2/3`), not a cycle;
F keyboard `B` = `VEHICLE_CAM` and `LOOK_BACK_CAM`; G six BmAK actions have no JC3 action name and
no vehicle module carries a keymap action (0/134); H `LT` battle threshold undecoded (`0.05`
constant, `0.2` DeadZone).

## Checks on this deliverable

* `Working/Q/PILOT/CONTROLS.md` and this report exist and carry the same 24 rows (compare the
  action column: 24 rows in each, no row without a source cell).
* Every row's source cell names a repo file; every non-file binding is labelled **UNKNOWN**.
* Canonical file adds the small-model rules (§3), including "never guess an UNKNOWN key".

Not done, by scope: no engine run, no keymap edit, no binding decisions made on the operator's
behalf — conflicts A–H are left with their settling check rather than a guess.
