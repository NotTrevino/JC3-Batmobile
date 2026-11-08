# ENTER_EXIT — get in (Y, fall back to E), check the camera and HUD, get out (E)

> change 2026-11-07 (review-pilot-cards): three defects. (1) Step 5 pressed `E` even when `Y` had
> already put Rico in the car, and `E` is also `EXIT_VEHICLE` — so the card could eject him and then
> score the exit frame as an entry. Step 5 is now conditioned on step 4 seeing no change. (2) Step 8
> copied `enter_y.png` regardless of which key worked; it now names the branch. (3) Step 10's heading
> and its command disagreed (`LB` vs `E`) and step 9 appended with `>>`; both are literal now.

GOAL: Rico is inside the Batmobile, the driving camera and the Batmobile HUD are on screen, and then
he is out again, with the frames archived and the key that worked on the RESULT line.

THE KEY CONFLICT THIS CARD SETTLES
`Working/Q/PILOT/CONTROLS.md` row 1 says enter is `E` (JC3 `ENTER_VEHICLE`, `decoded` from
`settings/keymap_keyboard.bin`) and marks the operator's `Y` as **UNKNOWN** (§2 conflict A), because
BmAK's `Y` is the afterburner (`bVehicleBoostButton`, `DefaultInput.ini:270`). The operator's live
mapping is also evidence (`GRAB_BACKLOG.md` D-11, marked `[CONFIRMED live]`), so this card presses
**Y first** and `E` second, and records which one entered. No other key is tried.

| action | key tried first | evidence | key tried second | evidence |
|---|---|---|---|---|
| enter | `Y` (`0x59`) | operator, D-11 `[CONFIRMED live]`; `CONTROLS.md` §2 conflict A | `E` (`0x45`) | `CONTROLS.md` row 1, `decoded` |
| exit | `LB` (BmAK pad) — keyboard fallback `E` (`0x45`) | `CONTROLS.md` row 2 (`LB` = `menu label`/live; `E`/`D-Pad Up` `decoded`) | — | — |

Laptop/keyboard pilots: `LB` is a gamepad button. If only a keyboard is attached, `LB` cannot be
pressed — record `LB not pressable` and use `E`; that is a hardware fact, not a judgement.

PRE-CONDITIONS
| # | check | command | must show |
|---|---|---|---|
| P1 | the car exists and is close | `Working/Q/PILOT/SPAWN_BATMOBILE.md` | `RESULT: PASS` |
| P2 | the process is the recorded one | `um win ps \| grep -i justcause3` | the same pid |
| P3 | a gamepad is attached, or accept the `E` fallback | operator / `um win ps` (no pad list in `um`) | stated on the RESULT line |

STEPS

### 1. Capture the approach
    DO   um win shot --exe JustCause3.exe Working/Q/PILOT/shots/enter_00.png
    SEE  the file exists, larger than 0 bytes
    IF NOT  STOP — capture dead, run SCREENSHOT step 7

### 2. Press Y once
    DO   um win drive --proc JustCause3 "key 0x59"
    SEE  `ok`
    IF NOT  `fail` -> STOP, the game is not foreground

### 3. Wait two seconds
    DO   sleep 2
    SEE  the command returns, exit 0
    IF NOT  re-run once

### 4. Capture after Y
    DO   um win shot --exe JustCause3.exe Working/Q/PILOT/shots/enter_y.png
    SEE  the file exists and its sha256 differs from `enter_00.png`
    IF NOT  identical -> run step 5
    IF NOT  it differs -> skip to step 8; do NOT press `E` here, because `E` is also `EXIT_VEHICLE` and would put Rico back out
    NOTE  the branch test is the hash comparison only (a change on screen), not a guess about the HUD

### 5. (only if step 4 saw no change) Press E once
    DO   um win drive --proc JustCause3 "key 0x45"
    SEE  `ok`
    IF NOT  `fail` -> STOP

### 6. Wait two seconds, then capture
    DO   sleep 2
    SEE  the command returns, exit 0
    IF NOT  re-run once

### 7. Capture after E
    DO   um win shot --exe JustCause3.exe Working/Q/PILOT/shots/enter_e.png
    SEE  the file exists and differs from `enter_00.png`
    IF NOT  identical -> neither key entered: STOP (report conflict A as unresolved on this build)

### 8. Freeze the in-car frame
    DO   cp Working/Q/PILOT/shots/enter_y.png Working/Q/PILOT/shots/enter_hud_ref.png
    SEE  the copy exists and `sha256sum` prints the same hash for both files
    IF NOT  the copy fails -> STOP (the repo is not writable)
    NOTE  if step 5 was the key that worked, copy `enter_e.png` instead and say so on the RESULT line.
    Whether the frame shows the driving HUD or the on-foot HUD is a HUMAN read, recorded as
    `observed (human): driving|on-foot`; the card does not claim to detect it.

### 9. Check the camera against the decoded rest pose
    DO   echo "rest: 7.00 m behind, 1.30 m above the pivot; FOV 55-63 vertical" > Working/Q/PILOT/shots/enter_camera.txt
    SEE  `wc -l` on that file prints `1` and the line matches the echo
    IF NOT  STOP — the repo is not writable
    NOTE the expected numbers are `CAMERA.md` §2b + `STATUS.md` (400 cm boom + additive sit offset;
    `55…63` from BmAK 85/95 horizontal → JC3 vertical). **Measuring** them is take A15
    (`T_PLAN.md` §5 A), not this card: JC3 exposes no telemetry, so this card archives the frame and
    cites the band; it does not pretend to read FOV from a PNG.

### 10. Exit with E (decoded `EXIT_VEHICLE`)
    DO   um win drive --proc JustCause3 "key 0x45"
    SEE  `ok`
    IF NOT  `fail` -> STOP
    NOTE  the card's machine path is `E`. `LB` is BmAK's menu label for exit and cannot be sent by
    `um win drive` (keyboard VKs only); with a pad the operator presses `LB` and the RESULT line
    records `operator press`, never a card step.

### 11. Wait two seconds, then capture
    DO   sleep 2
    SEE  the command returns, exit 0
    IF NOT  re-run once

### 12. Capture after exit
    DO   um win shot --exe JustCause3.exe Working/Q/PILOT/shots/exit_00.png
    SEE  the file exists and differs from the last in-vehicle frame
    IF NOT  identical -> the exit did not fire: repeat step 10 once, then STOP

### 13. Confirm the process and the dump folder
    DO   ls -t "$LOCALAPPDATA/CrashDumps" | grep -i justcause3 | head -1
    SEE  no output
    IF NOT  a dump name -> STOP with it on the RESULT line

RESULT
    RESULT: PASS — entered with <Y|E>, exited with E (or LB as an operator press) — pid=<pid> — shots/enter_00, enter_y, enter_e, enter_hud_ref, exit_00.png
    RESULT: STOP — step <n> — <the SEE that failed, quoted> — <artifacts so far>

TRAPS: E-1/E-2 (entry is a volume, not a point: the interaction trigger is 3.48 x 2.85 x 3.91 m and
the driver point sits beside the cockpit — approach **from the left**; if `Y`/`E` do nothing, first
check the side, not the key), K-1/K-2 (the operator's stated binding is `stated (user)`, so it is
tried and recorded, never asserted), and conflict A/B in `CONTROLS.md` §2 are the two checks this
card performs. JC3 has no telemetry, so entry/exit are calibrated-frame checks — the frames are the
evidence.
