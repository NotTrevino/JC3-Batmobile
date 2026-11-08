# PILOT CONTROLS — the Batmobile in JC3 (Q-PILOT step 3)

Purpose: one table a small model can follow without inventing a button. Two sources of truth,
kept apart:

* **JC3 side** — what the player can press in the drop. Read from JC3's own keymap files
  (`settings/keymap_keyboard.bin`, `settings/keymap_gamepad.bin`, patch layer) via
  `Research/JC3Grab/INPUT.md` (G3-08) and `Research/JC3Grab/INPUT_D11.md`.
* **BmAK side** — what the Batmobile's own scheme is: `BmGame/Config/DefaultInput.ini` lines via
  `Research/BatmobileGrab/CONTROLS.md`, `BINDINGS_KEYBOARD.md`, `BINDINGS_MERGED.md`, and the
  in-game controls screen transcribed in `Research/BatmobileGrab/CONTROLS_MENU_SCREENS.md`.

Rule from D-11 (`GRAB_BACKLOG.md`): **only entering the Batmobile uses JC3's control; everything
else uses BmAK's scheme.** Inside the Batmobile BmAK wins; JC3's pause and commlink keep priority
(operator note, `CONTROLS_MENU_SCREENS.md`). A binding is labelled `decoded` only when a file
carries it; `menu label` when only the BmAK controls screen names it; **everything else is
`UNKNOWN`** — including bindings the operator stated but no file contains.

## 1. Master table

`Screen after` = what is drawn/changed when the action fires. `menu` = the label on BmAK's own
controls screen (that label is what the game shows the player); `HUD` = a decoded
`RPlayerController.DrivingMode` function that runs (names in `CONTROLS_CONSUMERS.md` §States);
`UNKNOWN` = no screen record in any file.

| # | Action | Keyboard | Gamepad | What the screen shows after | Source file(s) | Label |
|---:|---|---|---|---|---|---|
| 1 | **Enter the Batmobile** | `E` (JC3 `ENTER_VEHICLE`) | `D-Pad Up` (JC3 `ENTER_VEHICLE`) | JC3's enter prompt is consumed and the Batmobile HUD replaces the on-foot HUD; BmAK's own screen lists no enter row | `Research/JC3Grab/INPUT.md` (ENTER_VEHICLE = RPADUP / E); `GRAB_BACKLOG.md` D-11 | decoded (JC3). Operator says "enter with JC3's Y" — **UNKNOWN**, §2 conflict A |
| 2 | **Exit the Batmobile** | `E` (JC3 `EXIT_VEHICLE`) | `D-Pad Up` (JC3 `EXIT_VEHICLE`); BmAK `LB` | menu: "Exit Batmobile"; Rico stands beside the car, camera returns to third person | `INPUT.md` (EXIT_VEHICLE); `CONTROLS_MENU_SCREENS.md` (LB = Exit Batmobile); `DefaultInput.ini:271` (LB = DualPlay); D-11 (LB live) | decoded for E / D-Pad Up; LB = **UNKNOWN** (`DualPlay`), §2 conflict B |
| 3 | **Accelerate** | `W` (JC3 `ACCELERATE`) | `RT` (`RTRIGGER`; BmAK `aThrottleAxis` on the same axis) | menu: "Accelerate"; speed rises, gear/speed HUD | `INPUT.md` (ACCELERATE = RTRIGGER / W); `CONTROLS.md` (aThrottleAxis, `DefaultInput.ini:254`); `CONTROLS_MENU_SCREENS.md` | decoded |
| 4 | **Brake / reverse** | `S` (JC3 `REVERSE`) | `LT` (`LTRIGGER`, JC3 `REVERSE`); BmAK `X` ("Brake / Reverse") | menu: "Brake / Reverse" (X); car slows then backs up | `INPUT.md` (REVERSE = LTRIGGER / S); `CONTROLS.md` (`bHandbrakeOrBrake`, `BrakePressed`, `DefaultInput.ini:269`); menu screen | decoded for S / LT; X = `UNKNOWN` in JC3 (§2 conflict C: LT is BmAK's battle-mode hold) |
| 5 | **Reverse** | `S` (JC3 `REVERSE`) | `LT` (JC3 `REVERSE`) | same as row 4 | `INPUT.md` | decoded |
| 6 | **Steer left / right** | `A` / `D` (JC3 `TURN_LEFT` / `TURN_RIGHT`) | `Left stick` left/right (JC3 `LSTICKLEFT` / `LSTICKRIGHT`) | menu: "Steer"; the car yaws, front wheels turn | `INPUT.md` (TURN_LEFT/RIGHT = LSTICKLEFT/RIGHT, A/D) | decoded |
| 7 | **Handbrake / drift** | `LShift` (JC3 `HANDBRAKE`) | `D-Pad Left` (JC3 `HANDBRAKE`); BmAK `X` (`bHandbrakeOrBrake`) | menu: "Power Slide" (left stick + RT + X); rear breaks loose, the car slides | `INPUT.md` (HANDBRAKE = RPADLEFT / LSHIFT); `CONTROLS.md` (`bHandbrakeOrBrake`); menu screen | decoded for LShift / D-Pad Left; BmAK's X-combo = `menu label` |
| 8 | **Boost / afterburner** | **UNKNOWN** — no JC3 action; `LShift` is `HANDBRAKE`, and `WINGSUIT_BOOST` is wingsuit-only | **UNKNOWN** — BmAK `Y` (`bVehicleBoostButton`, `DefaultInput.ini:270`) has no JC3 action name (JC3 has only `WINGSUIT_BOOST`) | menu: "Afterburner" (pursuit) / "Drone Virus" (battle, same Y); flame out the back, speed surge | `CONTROLS.md` (bVehicleBoostButton); `INPUT.md` §BmAK→JC3 ("nitro / afterburner" = UNKNOWN); menu screen | BmAK binding decoded, JC3 binding **UNKNOWN** |
| 9 | **Jump** | **n/a** — BmAK cannot jump (D-10: no JC3 gear mods) | **n/a** | nothing (JC3's `JUMP` is on-foot only) | `GRAB_BACKLOG.md` D-10; `INPUT.md` (JUMP = RPADDOWN / SPACE, scope on-foot) | decoded (absent by decision) |
| 10 | **60 mm cannon** (battle primary) | `LMB` (JC3 `FIRE_VEHICLE_WEAPON_PRIMARY`) | `RB` (JC3 `RSHOULDER`); BmAK `RT` | menu: "60mm Cannon" (RT); muzzle flash, cannon round, `DrawWeaponPowerLevel` HUD | `INPUT.md` (FIRE_VEHICLE_WEAPON_PRIMARY = RSHOULDER / MOUSE1); `CONTROLS.md` (`BatmobileFireButton`, `DefaultInput.ini:252`); menu screen; `CONTROLS_CONSUMERS.md` (DrawWeaponPowerLevel) | decoded (JC3 action); which BmAK weapon it is = `menu label` |
| 11 | **Vulcan gun** (battle secondary) | `RMB` (JC3 `FIRE_VEHICLE_WEAPON_SECONDARY`) | `LB` (JC3 `LSHOULDER`); BmAK `RB` | menu: "Vulcan Gun" (RB); tracer stream, heat/power bar | `INPUT.md` (FIRE_VEHICLE_WEAPON_SECONDARY = LSHOULDER / MOUSE2); `CONTROLS.md` (`SecondaryFireVehicleWeapon`, `bFireVehicleSecondaryWeapon`, `DefaultInput.ini:272`); menu screen | decoded (JC3 action); BmAK slot = `menu label` |
| 12 | **Tracker / immobilizer missile** (pursuit) | **UNKNOWN** — no JC3 action; near-name `USE_ITEM` (`E`) has no decoded vehicle consumer | **UNKNOWN** — BmAK `B` (`QuickGadgetB` → `SelectVehicleWeapon(1)`, `DefaultInput.ini:268`) | menu: "Tracker / Immobilizer"; target brackets, then the immobilizer missile fires | `CONTROLS.md` (QuickGadgetB = SelectVehicleWeapon 1); `CONTROLS_CONSUMERS.md` §2 (verdict UNKNOWN); `INPUT_D11.md` (USE_ITEM: 0 vehicle consumers); D-11 (B live) | **UNKNOWN** (§2 conflict D) |
| 13 | **Missile barrage** (battle) | **UNKNOWN** — no JC3 action | **UNKNOWN** — BmAK `X` (`QuickGadgetX` → `SelectVehicleWeapon(2)`, `DefaultInput.ini:269`) | menu: "Missile Barrage"; salvo launches, `DrawWeaponSelectHud` shows the salvo slot | `CONTROLS.md` (QuickGadgetX arg 2); `CONTROLS_CONSUMERS.md` (`DrawWeaponSelectHud` exists) | **UNKNOWN** |
| 14 | **Drone virus / hacker** (battle) | **UNKNOWN** — no JC3 action | **UNKNOWN** — BmAK `Y` (`QuickGadgetY` → `SelectVehicleWeapon(3)`, `DefaultInput.ini:270`) | menu: "Drone Virus"; drone locks up / turns on its owner | `CONTROLS.md` (QuickGadgetY arg 3) | **UNKNOWN** |
| 15 | **EMP burst** (battle) | **UNKNOWN** — no JC3 action | **UNKNOWN** — BmAK `B` (menu says "EMP"; D-11 calls the same button the immobilizer) | menu: "EMP"; blue pulse, affected vehicles stall | `CONTROLS_MENU_SCREENS.md` (battle: B = EMP); `GRAB_BACKLOG.md` D-11 (B = immobilizer) | **UNKNOWN**, and the two labels disagree (§2 conflict E) |
| 16 | **Sonar** | **UNKNOWN** — no JC3 `SONAR`/`SCAN` action | **UNKNOWN** — BmAK `L3` (`XboxTypeS_LeftThumbstick` → alias `BatmobileSonar`, `DefaultInput.ini:256`) | menu: battle d-pad lists "Scan"; sonar pulse, silhouettes through walls | `CONTROLS.md` (BatmobileSonarPressed, LeftThumbstick); `INPUT.md` (sonar/scan: not reachable) | **UNKNOWN** |
| 17 | **Weapon select 4 / missile pods** | **UNKNOWN** — no JC3 vehicle weapon-cycle action (`NEXT_WEAPON`/`PREV_WEAPON` are keyboard-only and unproven on a vehicle) | **UNKNOWN** — BmAK `D-Pad Up` (`SelectVehicleWeapon 4`, `DefaultInput.ini:259`) | `DrawWeaponSelectHud` switches the highlighted slot | `CONTROLS.md` (`SelectVehicleWeapon`, DPad_Up); `INPUT.md` §BmAK→JC3 (weapon selection = UNKNOWN) | **UNKNOWN** |
| 18 | **Mode switch: battle ↔ pursuit** | **UNKNOWN** — no JC3 action matches BATTLE/PURSUIT/TRANSFORM/MODE$ | **UNKNOWN** — BmAK `LT` hold = battle, release = pursuit (`aLeftTrigger`, `DefaultInput.ini:253`); the call path is undecoded | menu: "Battle Mode" (LT hold) / "Pursuit Mode" (LT release); armour plates fold, weapons swap | `CONTROLS_MENU_SCREENS.md`; `CONTROLS.md` (aLeftTrigger); `CONTROLS_CONSUMERS.md` §1 (verdict UNKNOWN); `INPUT.md` (not reachable); D-11 (live) | **UNKNOWN** (live-confirmed by operator, not in a file) |
| 19 | **Eject into glide** | **UNKNOWN** — JC3 `EJECT`/`LAUNCH` action does not exist | **UNKNOWN** — BmAK `A A` (`EjectFromVehicle` + `BattleStrafe`, `DefaultInput.ini:267`) | menu: "Eject Into Glide"; cockpit canopy blows, Rico is thrown into a glide | `CONTROLS_MENU_SCREENS.md`; `CONTROLS.md` (EjectFromVehicle); `CONTROLS_CONSUMERS.md` §5; D-11 (A exit items) | **UNKNOWN** |
| 20 | **Power winch** (gadget) | **UNKNOWN** — JC3 candidates `V` (`VEHICLE_RELEASE_GRAPPLE`) / `MMB` (`USE_VEHICLE_MOD`) | **UNKNOWN** — decision: `D-Pad Right` (operator, 2026-11-05) | cable leaves the car and pulls on whatever it is tethered to | `CONTROLS_MENU_SCREENS.md` (operator decision, replaces Mission Select); `INPUT.md` (VEHICLE_RELEASE_GRAPPLE = LPADDOWN / V; USE_VEHICLE_MOD = RPADRIGHT / MOUSE3) | **UNKNOWN** (design decision, no binding in a file) |
| 21 | **Driving camera** | `B` (JC3 `VEHICLE_CAM`) | `R3` (JC3 `VEHICLE_CAM`, `RSTICKBUTTON`); BmAK `C` / `RB` | menu: "Cycle View" (RB); camera cuts to the next vehicle view | `INPUT.md` (VEHICLE_CAM = RSTICKBUTTON / B); `CONTROLS.md` (ToggleDrivingCamera, `DefaultInput.ini:186`, `:272`) | decoded |
| 22 | **Look behind** | `B` (JC3 `LOOK_BACK_CAM`) — same key as `VEHICLE_CAM`, scope difference UNKNOWN | `R3` (BmAK `bLookBehindVehicle`, `DefaultInput.ini:255`) | menu: "Look Behind"; camera snaps backwards while held | `INPUT.md` (LOOK_BACK_CAM = RSTICKBUTTON / B); `CONTROLS.md` (bLookBehindVehicle) | decoded (key shared with row 21 — §2 conflict F) |
| 23 | **Pause menu / commlink (JC3 keeps priority)** | `Esc` (JC3 `GUI_PAUSE`), `Tab` (`GUI_PDA`) | `Start` (`GUI_PAUSE`), `Back` (`GUI_PDA`) | pause overlay; the map/commlink pane | `INPUT.md` (GUI_PAUSE = START / ESCAPE; GUI_PDA = BACK / TAB); `CONTROLS_MENU_SCREENS.md` (operator: JC3 pause/commlink keep priority) | decoded |
| 24 | **WayneTech / gadgets screen** (BmAK) | **UNKNOWN** — no JC3 action | **UNKNOWN** — BmAK View/back (`XboxTypeS_Back`, `DefaultInput.ini:261` → `OpenLevelUpOrMap`) | menu: "WayneTech"; the upgrade screen opens | `CONTROLS_MENU_SCREENS.md`; `CONTROLS.md` (OpenLevelUpOrMap) | **UNKNOWN** |

Every BmAK weapon in the tree is covered: cannon (10), Vulcan (11), tracker + EMP missile (12),
EMP burst (15), hacker/drone virus (14), sonar (16), barrage (13), missile pods/weapon 4 (17),
riot mode (below). The booster mesh (priority 2) is the visual of row 8; the EMP burst shares
row 15. **Riot mode** (non-lethal suppressor) is a named omission — D-3 accepted JC3 lethality, so
it has no binding and no row: `GRAB_BACKLOG.md` D-3.

## 2. Conflicts and gaps, with what settles each

Each item names the file that settles it and a one-sentence pilot-card check. Nothing here may be
filled in from memory.

**A. Enter: operator says "Y", the file says `E` / `D-Pad Up`.**
`Research/JC3Grab/INPUT.md` decodes `ENTER_VEHICLE` = `RPADUP` (pad) / `E` (keyboard) from
`settings/keymap_*.bin`. `CONTROLS_MENU_SCREENS.md` records "Enter with JC3's Y" (operator).
`GRAB_BACKLOG.md` D-11 records "LB = exit AND enter [CONFIRMED live]". Three different answers —
in JC3 `Y` is not an enter action, and BmAK's `Y` is the afterburner (row 8), so binding `Y` to
enter would take the boost away.
Settles: `Research/JC3Grab/INPUT.md` §action table + `GRAB_BACKLOG.md` D-11.
Check: stand beside a parked car in JC3 and press `Y` — if nothing happens and `E` enters, the
file is right and the operator note meant "the button JC3 shows on its prompt".

**B. Exit: BmAK's `LB` does not exit in BmAK's own config.**
`DefaultInput.ini:271` binds `LB` (`XboxTypeS_LeftShoulder`) to `DualPlay` → `DualPlayPressed`
(17 bytes, no exit call). `CONTROLS_CONSUMERS.md` §4 says the route from `DualPlayPressed` to
`DualPlayAction`/exit is undecoded, while the operator observed LB exiting (D-11, live).
Settles: `Research/BatmobileGrab/CONTROLS_CONSUMERS.md` §4 + D-11.
Check: in BmAK, press LB with the Batmobile stopped — if Rico steps out, LB is the exit whatever
`DualPlay` means; if not, exit is `A`-adjacent and D-11's LB row is wrong.

**C. Brake on `X` (BmAK) has no JC3 action; `LT` is both reverse (JC3) and battle-mode hold (BmAK).**
`DefaultInput.ini:269` puts `BrakePressed` / `bHandbrakeOrBrake` on `X`; JC3's `REVERSE` is `LT`.
Binding `LT` to battle mode (D-11) would consume JC3's reverse.
Settles: `Research/JC3Grab/INPUT.md` (`REVERSE`, `HANDBRAKE`) + `CONTROLS.md` (X row).
Check: reverse the car with `LT` held slightly — if it backs up and no armour transforms, mode and
reverse are fighting for one axis and one of them must move.

**D. B: tracker/immobilizer (D-11) vs EMP (BmAK's own battle screen).**
`CONTROLS_MENU_SCREENS.md` battle column: `B` = EMP; pursuit column: `B` = Tracker / Immobilizer.
D-11 says B = immobilizer on an auto-tagged enemy. Both go through `QuickGadgetB` →
`SelectVehicleWeapon(1)` (`DefaultInput.ini:268`), i.e. the same slot index.
Settles: `Research/BatmobileGrab/CONTROLS.md` (QuickGadgetB) + `CONTROLS_MENU_SCREENS.md`.
Check: in each mode press `B` once — if the same projectile leaves the car in both modes, the
per-mode difference is the weapon equipped in slot 1, not the button.

**E. Battle weapon switch is `SelectVehicleWeapon(2)` / `(3)`, not a cycle.**
`QuickGadgetX` passes 2 and `QuickGadgetY` passes 3; `ReleaseVehicleWeapon` releases them. So
"barrage" and "drone virus" are *selected* slots, not separate keys — which is why rows 13/14
cannot be split further without a decoded slot table.
Settles: `Research/BatmobileGrab/CONTROLS.md` (SelectVehicleWeapon, ReleaseVehicleWeapon) and
`GRAB_BACKLOG.md` D-7 (every weapon in both modes).
Check: fire after tapping `X` then `RT` — if the next shot is the barrage, X selects and RT fires.

**F. `B` is three different things on the keyboard side.**
JC3 binds `VEHICLE_CAM` to `B` (keyboard) and `LOOK_BACK_CAM` to `B`; the Batmobile does not read
keyboard at all in BmAK. Which of the two JC3 rows wins inside a vehicle is undecoded.
Settles: `Research/JC3Grab/INPUT.md` §UNKNOWN (keymap layer/consumer) — no file resolves it.
Check: sit in a vehicle and tap `B` — if the view cycles, `VEHICLE_CAM` wins; if it looks behind
while held, `LOOK_BACK_CAM` wins.

**G. Mode switch, boost, ejection, sonar and every BmAK weapon have no JC3 action name at all.**
`Research/JC3Grab/INPUT.md` §BmAK actions → JC3: battle mode, ejection, sonar, tag gun, barrage,
nitro = **not reachable / UNKNOWN**; `Research/JC3Grab/INPUT_D11.md`: 0 of 134 decoded vehicle
modules reference any keymap action. The only button→action tables are `settings/keymap_*.bin`,
and no entity names them (0/232 dumps contain `keymap`).
Settles: `Research/JC3Grab/INPUT.md` §"What an entity or module can change without code".
Check: add one action id to `settings/keymap_keyboard.bin`, drop it in, press the key in a vanilla
car — if a script-visible effect fires, a dropzone keymap is honoured; if not, the route is native
and these six rows cannot be bound by data.

**H. `LT` battle hold has no decoded threshold.**
`CONTROLS_CONSUMERS.md` §1: the only float near `aLeftTrigger`/`LastTriggerAmount` is `0.05`
(offset 257, `IsBatmobileFireButtonHeld`) and the ini DeadZone is 0.2 (`DefaultInput.ini:253`);
the operator path to `TryToChangeMode` is undecoded.
Settles: `Research/BatmobileGrab/CONTROLS_CONSUMERS.md` §1 + `D-11` live note.
Check: hold `LT` progressively — note the amount at which the armour transforms; if it is not 0.05
or 0.2 the threshold is elsewhere.

## 3. Rules for a small model using this file

1. If an action's row says `UNKNOWN`, do **not** guess a key. Point at the settling file in §2.
2. `decoded` rows may be quoted as-is; `menu label` rows describe BmAK, not a JC3 binding.
3. Never move `Pause`/`commlink` off JC3's `Esc`/`Tab`/`Start`/`Back` — the operator keeps JC3
   priority there (§1 row 23).
4. Never bind `Y` to enter while row 8 needs `Y` for boost; resolve conflict A first.
5. `settings/keymap_*.bin` is the only button→action table (patch layer wins a path lookup);
   changing it is untested from a dropzone (INPUT.md §UNKNOWN).

## 4. Evidence files (all in this repo)

| file | what it is |
|---|---|
| `Research/JC3Grab/INPUT.md` | JC3 keymap decode: 474 bindings, 154 actions, per-action device table (G3-08) |
| `Research/JC3Grab/INPUT_D11.md` | D-11 actions vs 134 decoded vehicle modules (0 hits) |
| `Research/BatmobileGrab/CONTROLS.md` | BmAK ini action table (token → key/pad → source line) |
| `Research/BatmobileGrab/CONTROLS_CONSUMERS.md` | BmAK script walks: LT / B / LB / A verdicts |
| `Research/BatmobileGrab/CONTROLS_MENU_SCREENS.md` | BmAK's in-game controls screen, transcribed (pursuit + battle) and the operator notes |
| `Research/BatmobileGrab/BINDINGS_KEYBOARD.md` / `BINDINGS_MERGED.md` | raw BmAK chain + merge rule (BmInput.ini is not in this repo; the merged array is the oracle) |
| `GRAB_BACKLOG.md` D-11 | the D-11 control decision and the operator's live mapping |
