# LOAD_SAVE — from the main menu into free roam on the operator's own save

> change 2026-11-07 (review-pilot-cards): step 8 read as an unconditional step although it only
> applies when step 7 saw no change; a pilot following the card in order would click the menu after
> it had already loaded. The step is now conditioned on step 7's SEE and on nothing else.

GOAL: the game is in free roam on the operator's save, the save is backed up and unchanged, and the
PID is the one LAUNCH recorded.

WHICH SAVE (evidence, not a choice)
The save root is `C:\Users\User\Documents\Square Enix\Just Cause 3\Saves` and holds exactly two
folders and 50 files (counted 2026-11-06):

| path | what it is | evidence |
|---|---|---|
| `Saves\0\settings.json` | machine settings, not a profile slot | directory listing of the save root, 2026-11-06 |
| `Saves\76561197960271872\` | **the player profile** (Steam ID folder): `player_save_data`, `tasks`, `items`, `feats`, `chaos_storage`, `unlocked_resupply_points`, `statistics_pending`, … | same listing; `player_save_data` is the slot file |
| `um backup list` → `jc3-saves 20261031-210237.zip 50 files C:\Users\User\Documents\Square Enix\Just Cause 3` | the snapshot this card checks against | `um backup list`, 2026-11-06 |

So "which save" = the only profile folder, `76561197960271872`, in-game **slot 1**; there is no
second profile on this machine. The menu **label** of that slot is `UNKNOWN` in this repo (no file
records JC3's main-menu entries — grep for `main menu`/`load game` in `MODLOG.md` returns only the
QA-1 take description, no labels).

CALIBRATION (fill on the first run of this card; it is blank in a fresh checkout)
    ENTER_KEY=<one WinDrive `key 0x..` that accepts the highlighted main-menu item>
    SAVE_SLOT_CLICK=<x y inside the client area that selects slot 1>
Source for both: UNKNOWN — measured once by the operator on the first run, then fixed here. No key
is guessed: this card refuses to run on a guessed key.

PRE-CONDITIONS
| # | check | command | must show |
|---|---|---|---|
| P1 | approval to launch | `test -f tmp/freebuff/APPROVED_Q.txt && echo YES` | `YES` |
| P2 | LAUNCH card PASS | `Working/Q/PILOT/LAUNCH.md` RESULT line | `RESULT: PASS` with a pid |
| P3 | calibration done | `grep -E "^    (ENTER_KEY|SAVE_SLOT_CLICK)=<" Working/Q/PILOT/LOAD_SAVE.md` | no output (the placeholders are gone) |

STEPS

### 1. Confirm the backup is the newest snapshot
    DO   um backup list | grep jc3-saves
    SEE  one line, count `>= 50 files`
    IF NOT  no line -> run LAUNCH step 1 first, then restart this card

### 2. Count the save files on disk
    DO   find "C:/Users/User/Documents/Square Enix/Just Cause 3" -type f | wc -l
    SEE  `50`
    IF NOT  a different number -> the save changed since the backup: re-run LAUNCH step 1, then this step

### 3. Confirm the slot file exists and is non-empty
    DO   ls -l "C:/Users/User/Documents/Square Enix/Just Cause 3/Saves/76561197960271872/player_save_data"
    SEE  one line, size larger than 0
    IF NOT  missing -> STOP, the profile was moved or deleted; restore with `um backup restore jc3-saves --yes`

### 4. Capture the menu before any input
    DO   um win shot --exe JustCause3.exe Working/Q/PILOT/shots/load_menu.png
    SEE  the file exists, larger than 0 bytes
    IF NOT  STOP — see LAUNCH step 10

### 5. Accept the highlighted menu item with the calibrated key
    DO   um win drive --proc JustCause3 "key <ENTER_KEY>"
    SEE  `ok`
    IF NOT  `fail` -> the game is not foreground: STOP and re-run LAUNCH step 8

### 6. Wait for the load
    DO   sleep 20
    SEE  the command returns, exit 0
    IF NOT  interrupted -> re-run once

### 7. Capture after the load
    DO   um win shot --exe JustCause3.exe Working/Q/PILOT/shots/load_after.png
    SEE  the file exists and its sha256 differs from `load_menu.png`
    IF NOT  identical -> nothing was accepted: run step 5 once more with the same key, then STOP

### 8. (only if step 7's SEE failed) Click the save slot
    DO   um win drive --proc JustCause3 "click <SAVE_SLOT_CLICK>"
    SEE  `ok`, then steps 6-7 again
    IF NOT  still the same frame after two attempts -> STOP, the menu layout differs from the calibration

### 9. Confirm the process is unchanged
    DO   um win ps | grep -i justcause3
    SEE  the same pid as LAUNCH step 7
    IF NOT  STOP — the game restarted or died

### 10. Confirm no crash dump appeared
    DO   ls -t "$LOCALAPPDATA/CrashDumps" | grep -i justcause3 | head -1
    SEE  no output
    IF NOT  a dump name is printed -> STOP with the dump name on the RESULT line

### 11. Freeze the in-game reference frame
    DO   cp Working/Q/PILOT/shots/load_after.png Working/Q/PILOT/shots/load_ref.png
    SEE  both files exist
    IF NOT  STOP

RESULT
    RESULT: PASS — free roam on profile 76561197960271872, 50 save files intact — pid=<pid> — shots/load_menu.png, shots/load_after.png, shots/load_ref.png
    RESULT: STOP — step <n> — <the SEE that failed, quoted> — <artifacts so far>

TRAPS: L-2 (a dump, not a hunch), A-1 is not relevant here but the save backup is: a scripted take
can destroy a save, so P1/step 1 come first. JC3 exposes no telemetry (`QA1_RESULTS.md` §1), so
"in free roam" is a frame the pilot archives, not a value it can query — the card never claims to
read game state.
