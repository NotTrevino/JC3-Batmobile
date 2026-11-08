# SCREENSHOT — one frame on disk, with proof the capture is live

> change 2026-11-07 (review-pilot-cards): the `shot1` placeholder sat inside four commands, so the
> card could not be copy-pasted and the pilot had to invent a filename (a judgement call). It is now
> the literal `shot1`. Step 5 also states the scanmode dependency LAUNCH step 19 proves.

GOAL: one named frame of the running game on disk, and a proven-live capture oracle, so no
observation in this session rests on a frozen picture.

PRE-CONDITIONS
| # | check | command | must show |
|---|---|---|---|
| P1 | LAUNCH card PASS | `Working/Q/PILOT/LAUNCH.md` RESULT line starts `RESULT: PASS` | PASS with a pid |
| P2 | the process is the one LAUNCH recorded | `um win ps \| grep -i justcause3` | the same `<pid>` |

STEPS

### 1. Make the shot directory
    DO   mkdir -p Working/Q/PILOT/shots
    SEE  exit 0
    IF NOT  STOP — repo not writable

### 2. Capture the frame (also writes a 1/3-size copy)
    DO   um win shot --exe JustCause3.exe --scale 0.33 Working/Q/PILOT/shots/shot1.png
    SEE  exit 0 and `Working/Q/PILOT/shots/shot1.png` exists, larger than 0 bytes
    IF NOT  STOP — no window matched; verify P2

### 3. List what was written
    DO   ls -l Working/Q/PILOT/shots/ | grep shot1
    SEE  at least two files: the full frame and the scaled copy (write both names on the RESULT line)
    IF NOT  only one file -> continue with the full frame only, and note it on the RESULT line

### 4. Print the frame size
    DO   python -c "import struct;d=open('Working/Q/PILOT/shots/shot1.png','rb').read(24);print(struct.unpack('>II',d[16:24]))"
    SEE  a tuple printed; it must equal the size LAUNCH step 11 printed
    IF NOT  different size -> the window changed since LAUNCH: STOP, re-run LAUNCH step 8

### 5. Open the pause overlay (a guaranteed screen change)
    DO   um win drive --proc JustCause3 "key 0x1B"
    SEE  `ok`
    IF NOT  `fail` -> the game is not foreground: re-run LAUNCH step 19, then this step once; a second `fail` -> STOP
    IF NOT  `ok` but step 6's frame is unchanged -> re-run LAUNCH step 19 (`scanmode on`) and this step once, then STOP

### 6. Capture the changed frame
    DO   um win shot --exe JustCause3.exe Working/Q/PILOT/shots/shot1_esc.png
    SEE  the file exists, larger than 0 bytes
    IF NOT  STOP

### 7. Compare the two frames
    DO   sha256sum Working/Q/PILOT/shots/shot1.png Working/Q/PILOT/shots/shot1_esc.png
    SEE  two different hashes — the oracle is live
    IF NOT  identical hashes -> frozen capture (upstream trap): STOP, no frame from this session may be interpreted

### 8. Close the overlay
    DO   um win drive --proc JustCause3 "key 0x1B"
    SEE  `ok`
    IF NOT  STOP — the game is left paused; go to KILL

### 9. Confirm the game is still the same process
    DO   um win ps | grep -i justcause3
    SEE  the same pid as P2
    IF NOT  STOP

RESULT
    RESULT: PASS — live capture proven, frame on disk — pid=<pid> — Working/Q/PILOT/shots/shot1.png (+ scaled copy)
    RESULT: STOP — step <n> — <the SEE that failed, quoted> — <artifacts so far>

TRAPS: frozen oracle (`oracles-how-agents-know-a-mod-works.md`; a capture that repeats
byte-identically inverts every conclusion), R-1/R-2 (a number read off the HUD is not a
measurement until a human-read frame validates it — this card only stores frames, it reads
nothing). Key used: `Esc` = JC3 `GUI_PAUSE`, `decoded` (CONTROLS.md row 23) — no UNKNOWN key is
pressed.
