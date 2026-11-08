# LAUNCH — cold start to the main menu

> change 2026-11-07 (review-pilot-cards): step 12 claimed to see a timing (`returns after about
> 120 s`) that no tool reports — it now checks the exit code only. Step 19 is new: it sends
> `scanmode on` once, because the WinDrive source records that one down+up SendInput is shorter than
> a frame and that DirectInput/raw-input games need scanmode. Every later card's key press depends
> on this step.

GOAL: saves snapshotted, installer green, and JC3 running in a 1600x900 window at the main menu,
with the PID written down.

PRE-CONDITIONS (all must hold before step 1)
| # | check | command | must show |
|---|---|---|---|
| P1 | operator approval to launch exists | `test -f tmp/freebuff/APPROVED_Q.txt && echo YES` | `YES` (absent -> STOP, the test ban still stands) |
| P2 | the game is not already running | `um win ps \| grep -i justcause3` | no line |
| P3 | this is the first launch since the machine started | operator confirms | `yes` (one launch per boot) |

STEPS

### 1. Snapshot the saves
    DO   um backup create "C:\Users\User\Documents\Square Enix\Just Cause 3" --name jc3-saves
    SEE  exit 0 and a printed snapshot path ending `.zip` with a file count `>= 50`
    IF NOT  STOP — no backup exists, the game must not start

### 2. Confirm the snapshot is listed
    DO   um backup list | grep jc3-saves
    SEE  one line: `jc3-saves <YYYYMMDD-HHMMSS>.zip` and a count `>= 50 files`
    IF NOT  STOP — the snapshot in step 1 did not land

### 3. Prove the installer offline (allow up to 10 minutes)
    DO   python Tools/scripts/install_v3.py --check
    SEE  final line `CHECK_EXIT=0` (preceded by `PASS: ...`)
    IF NOT  a line starting `FAIL:` — copy that whole line onto the RESULT line and STOP

### 4. Verify the simulated dropzone against the receipt
    DO   pwsh Working/Installer/install_v3.ps1 -Action Verify -GameDir 'E:\Modding\JustCause3\_dropzone_sims\_dropzone_sim_rc2_v3'
    SEE  `verified 9/9` and exit 0
    IF NOT  `REFUSED:` or "no dropzone" — re-run step 3 (it rebuilds the sims), then this step once; a `BAD` line -> STOP

### 5. Verify the real dropzone, read-only
    DO   pwsh -File Builds/bm-RC2/install.ps1 -Action Verify -GameDir 'D:\Games\Just Cause 3'
    SEE  `verified 9/9` and exit 0
    IF NOT  any `BAD`/`absent` line -> STOP — installing is not a pilot step

### 6. Start the game with the archive flags
    DO   um win launch "D:\Games\Just Cause 3\JustCause3.exe" -- --vfs-fs dropzone --vfs-archive patch_win64 --vfs-archive archives_win64 --vfs-archive dlc_win64 --vfs-fs .
    SEE  exit 0
    IF NOT  STOP — note the exact error text; do not retry more than once

### 7. Read the PID
    DO   um win ps | grep -i justcause3
    SEE  exactly one line, first column is the PID — write it on the RESULT line
    IF NOT  no line -> the game died during init: go to KILL step 1 only if a PID still exists, otherwise STOP and report
    IF NOT  two lines -> STOP, two instances exist

### 8. Set the fixed window size
    DO   um win drive --proc JustCause3 "size 1600 900"
    SEE  `ok`
    IF NOT  `fail` — the game is fullscreen: JC3 Options -> Video -> Windowed, back to the game, re-run this step once; second `fail` -> STOP

### 9. Measure the frame
    DO   mkdir -p Working/Q/PILOT/shots
    SEE  the directory exists (exit 0)
    IF NOT  STOP — the repo is not writable from this shell

### 10. Capture the first frame
    DO   um win shot --exe JustCause3.exe Working/Q/PILOT/shots/launch_a.png
    SEE  the file exists and is larger than 0 bytes
    IF NOT  STOP — no window matched `JustCause3.exe`; check step 7's PID still exists

### 11. Print the frame size
    DO   python -c "import struct;d=open('Working/Q/PILOT/shots/launch_a.png','rb').read(24);print(struct.unpack('>II',d[16:24]))"
    SEE  a tuple printed; write it on the RESULT line
    IF NOT  a struct/tuple error -> STOP (the capture is not a PNG)

### 12. Wait for init to finish
    DO   sleep 120
    SEE  exit 0 (the card makes no claim about the elapsed time: `sleep` has no timing oracle)
    IF NOT  non-zero exit -> re-run it once, then STOP

### 13. Capture frame B
    DO   um win shot --exe JustCause3.exe Working/Q/PILOT/shots/launch_b.png
    SEE  the file exists and is larger than 0 bytes
    IF NOT  STOP — rendering stopped; go to KILL

### 14. Wait ten seconds
    DO   sleep 10
    SEE  the command returns, exit 0
    IF NOT  re-run it once

### 15. Capture frame C
    DO   um win shot --exe JustCause3.exe Working/Q/PILOT/shots/launch_c.png
    SEE  the file exists and is larger than 0 bytes
    IF NOT  STOP — go to KILL

### 16. Prove the picture changes
    DO   sha256sum Working/Q/PILOT/shots/launch_b.png Working/Q/PILOT/shots/launch_c.png
    SEE  two different hashes
    IF NOT  identical hashes -> the capture is frozen (upstream trap): STOP, no frame from this session may be interpreted

### 17. Confirm the same process is still alive
    DO   um win ps | grep -i justcause3
    SEE  the same PID as step 7
    IF NOT  STOP — the process changed or died

### 18. Confirm there is no new crash dump
    DO   ls -t "$LOCALAPPDATA/CrashDumps" | grep -i justcause3 | head -1
    SEE  no output (no dump)
    IF NOT  a dump name is printed -> STOP and put `JustCause3.exe.<pid>.dmp` on the RESULT line (catalogue L-2)

### 19. Put WinDrive into scan mode for the rest of the session
    DO   um win drive --proc JustCause3 "scanmode on"
    SEE  `ok`
    IF NOT  `fail` -> the game is not foreground: re-run steps 7-8 once, then STOP
    NOTE  source: the WinDrive command list (`pilot-study-universal-modder.md` §1, `skills/game-automation`)
    records `scanmode on` for DirectInput/raw-input games and says one `SendInput` with down+up is
    shorter than a frame. Whether JC3 needs scanmode is **UNKNOWN** in this repo, so this step sends it
    once rather than asserting it: if a later card's key press returns `ok` and nothing changes on
    screen, that card re-sends this step once before it STOPs.

RESULT
    RESULT: PASS — main menu reached, window size command accepted — pid=<pid> — Working/Q/PILOT/shots/launch_a,b,c.png + frame size from step 11
    RESULT: STOP — step <n> — <the SEE line that failed, quoted> — <artifacts so far>

TRAPS: L-1 (launch, then record — never start a capture before the menu), L-2 (read the dump
signature before blaming the build), L-4 (one launch per boot), K-1 (no key is pressed here).
Notes: the frame size from step 11 is recorded, not asserted — the capture may include the window
border, so the card requires a *stable* size (steps 11/13/15) rather than an exact 1600x900. A
JC3 launch flag for windowed mode is **UNKNOWN** in this repo; the size is set through WinDrive,
which is a documented `size <w> <h>` command.
