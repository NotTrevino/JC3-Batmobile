STATUS: done. Four cards written; nothing launched, installed, captured or killed (no
`tmp/freebuff/APPROVED_Q.txt`). Every menu state and every coordinate in the cards is either cited
to a repo file or marked UNKNOWN; nothing was filled from memory.

# Q-PILOT step 5 — getting a vehicle under the player

Deliverables (all in this repo):

| file | what it is | steps |
|---|---|---|
| `Working/Q/PILOT/LOAD_SAVE.md` | which save, and how to load it | 11 |
| `Working/Q/PILOT/SPAWN_BATMOBILE.md` | the Rebel Drop entry as `bm_rebel.py` built it + every screen observed | 10 |
| `Working/Q/PILOT/ENTER_EXIT.md` | enter with `Y` (fallback `E`), camera/HUD frame, exit `LB` (fallback `E`) | 13 |
| `Working/Q/PILOT/AIRFIELD.md` | find and *prove* the straight test strip | 10 |
| `Working/Q/PILOT/CARD_FORMAT.md` | §4 index updated; new §4a "calibration fields" | — |

## 1. LOAD_SAVE — which save

Counted on disk 2026-11-06, and cross-checked against the backup the LAUNCH card already takes:

| fact | value | source |
|---|---|---|
| save root | `C:\Users\User\Documents\Square Enix\Just Cause 3` | directory listing; same path in `um backup list` |
| profile folder (the save) | `Saves\76561197960271872\` — the only player folder | listing; slot file `player_save_data` |
| second folder | `Saves\0\settings.json` — machine settings, not a slot | listing |
| files | 50 | `find … -type f \| wc -l` = 50; `um backup list` says `50 files` |
| snapshot | `jc3-saves 20261031-210237.zip` | `um backup list` |

**UNKNOWN:** the main-menu label of that slot. `grep -i "main menu|load game|continue"` over
`MODLOG.md` returns only the QA-1 take description ("recorded … from the main menu") and unrelated
lines — no menu text is recorded anywhere in the repo. The card therefore refuses to name the
button: `ENTER_KEY` and `SAVE_SLOT_CLICK` are calibration fields, and P3 blocks the run until they
hold values.

## 2. SPAWN_BATMOBILE — the menu as `bm_rebel.py` built it

Every built field is quoted from `Tools/scripts/bm_rebel.py` (the script is the source of record for
the entry): `Name`/`UIName` = `hash(leaf) = 443190071`; `UIDescription` = `hash(leaf+"_desc")`;
`UIDisplayOrder` 12 (`jc3rebeldrop` `free_order`, max+1); `UIFlag 7` / `UIFlagDescription 1492769243`
(the vanilla armoured group: armouredjeep, armouredtransport, technicaljeep, buggy rebel — operator
decision "military, not sports", 2026-11-02); `UIImagePath` = new leaf with the donor `.ddsc`
byte-copied; `UIVideoPath` = donor string kept (UNKNOWN in the UI); unlock = `+1 ItemReward` on the
repeatable reward of task `1980624442` (vanilla starter grant); plus the `spawn_vehicle_defs.bin`
record with `tags vehicle,batmobile`, `select 1`, `debug vehicle|ground|rebel`.

The card lists **six screens**, each with its literal text and its source:

| # | screen | shows | source |
|---|---|---|---|
| 1 | main menu | UNKNOWN (no labels in repo) | grep, 2026-11-06 |
| 2 | Rebel Drop list | row **BATMOBILE**, donor icon, military group | `MODLOG.md` Q-1a "\"BATMOBILE\" present in Rebel Drop -> PASS"; `NAMES.md` (name resolves via `profile/online.stringlookup`) |
| 3 | LOCKED (historical build) | `Bring to garage` | `MODLOG.md` Q-1a |
| 4 | no reward (historical) | `Err: No Valid locking reason` | `MODLOG.md` Q-1a re-test 2 |
| 5 | selected, nothing arrives (historical) | empty drop | `MODLOG.md` Q-1a re-test 2 / probe 2, B-13c |
| 6 | delivered | the car drops in | `MODLOG.md` Q-1a re-test 3 (screenshot `Captures/Just Cause 3 11_2_2026 4_42_02 AM.png`) |

Offline proof comes first and is exact: `python Tools/scripts/bm_rebel.py --check` prints
`item.onlinec decodes: 196 -> 197 items, 1 Batmobile` and ends `PASS: B-13 0 failure(s)` (both
strings read from the script's own `check()`). The navigation from screen 1 to screen 2 is UNKNOWN,
so it is the three calibration fields.

## 3. ENTER_EXIT — Y per the operator, E per the file

The request said "enter with Y per the controls reference"; the reference itself says the opposite,
and the card states the conflict rather than picking a side:

* `CONTROLS.md` row 1: enter = `E` / `D-Pad Up` (`ENTER_VEHICLE`, `decoded`); `Y` is **UNKNOWN**
  (§2 conflict A), because BmAK's `Y` is the afterburner (`bVehicleBoostButton`,
  `DefaultInput.ini:270`).
* `GRAB_BACKLOG.md` D-11 records the operator's mapping live (`[CONFIRMED live]`).

Step order: `Y` (`0x59`) first, `E` (`0x45`) second; exit `LB` with `E` as the keyboard fallback
(also recorded as a conflict: `LB` = `DualPlay` in `DefaultInput.ini:271`, §2 conflict B). The RESULT
line names which key worked, which is precisely the check conflict A asks for.

Camera/HUD after entering: the card archives `enter_hud_ref.png` and writes the expected values —
rest 7.00 m behind / 1.30 m above the pivot, FOV 55–63 vertical (`CAMERA.md` §2b, `STATUS.md`,
T-CAM5/T-CAM2). It does **not** claim to measure them from a PNG: JC3 has no telemetry
(`QA1_RESULTS.md` §1), and measuring them is take A15 (`T_PLAN.md` §5 A). That is stated in the step.

## 4. AIRFIELD — the honest answer

**The QA-1 airfield coordinates are not in this repo.** Evidence:

* `grep -i "airfield|airstrip|falco|coordinate" MODLOG.md` → no location row (only unrelated
  `SphericalCoordinateFramingParams`, an archive-tile note, and "not given invented coordinates").
* `Working/Translation/QA1_RESULTS.md` records take, time, build, instrument and measurements — no
  location field.
* The requirement is stated without a place: "flat airfield, straight, dry, no traffic"
  (`QA1_RESULTS.md` §7, take A2 entry conditions); "Session 2 — driving takes at the airfield"
  (`Research/specs/Q-2.md`, `GRAB_BACKLOG.md:1473`).
* The only airfield asset named anywhere is a DLC map,
  `dlc/mech_land_assault/locations/island/dlc2_processing_facility_airstrip.*`
  (`Research/JC3Grab/INDEX.jsonl`) — whether that is the 2026-10-22 location is UNKNOWN.

So the card navigates once (`STRIP_START`, calibrated) and then **proves the strip from the take**,
using the repo's own instrument: `qa1_hud.py crops → build → trace`, then two numeric gates on the
trace — no speed drop beyond 5 km/h between 0.2 s samples (D-1's off-road signature is 64 → 0 in
1.2 s) and a covered length ≥ the calibrated requirement. That is the only location fact the repo
can supply, and it is measurable.

## 5. Calibration fields (new rule in `CARD_FORMAT.md` §4a)

Three cards needed a navigation fact the repo does not contain. Rather than guess, each carries a
field valued `UNKNOWN` and a pre-condition that blocks the run until the field holds a value; the
first run is a calibration run where the operator performs the action once and writes it in. This is
the only legal use of `UNKNOWN` inside a card, and it is now written into the format page:
`LOAD_SAVE.md` (`ENTER_KEY`, `SAVE_SLOT_CLICK`), `SPAWN_BATMOBILE.md` (`OPEN_DROP`,
`DROP_ENTRY_CLICK`, `CONFIRM_CLICK`), `AIRFIELD.md` (`STRIP_START`, two reference shots,
`STRIP_LENGTH_M`).

## 6. Checks run

`Working/Q/PILOT/` structural check (same script as step 4): every `### N.` step carries exactly one
`DO`, one `SEE` and at least one `IF NOT`; every card has `GOAL`, `PRE-CONDITIONS` and a `RESULT`
line. Results are printed in the terminal transcript of this session; `LOAD_SAVE` 11, `SPAWN_BATMOBILE`
10, `ENTER_EXIT` 13, `AIRFIELD` 10 steps, all matched.

Sources read for this card, no launch: the save root listing (50 files), `um backup list`,
`Tools/scripts/bm_rebel.py`, `Research/specs/Q-2.md`, `Working/Translation/QA1_RESULTS.md`,
`Working/Translation/T_PLAN.md` §5A, `MODLOG.md` (Q-1a chain, QA-1 take), `Research/JC3Grab/REBELDROP.md`,
`NAMES.md`, `INDEX.jsonl`. No game file, no dropzone, no git.

**Not done, by scope:** `DRIVE.md` and `FIGHT.md` (the last two Q-PILOT cards), the DeepSeek
read-through, and the calibration runs themselves (they need the game). `install_v3.py --check`
still has not been observed passing — it timed out at 240 s in step 4 and LAUNCH requires its
literal `CHECK_EXIT=0` rather than claiming it green.

## 7. Revert

Delete `Working/Q/PILOT/{LOAD_SAVE,SPAWN_BATMOBILE,ENTER_EXIT,AIRFIELD}.md`, revert the §4 table and
§4a addition in `CARD_FORMAT.md`, and remove the MODLOG section that records them. No other file was
modified.
