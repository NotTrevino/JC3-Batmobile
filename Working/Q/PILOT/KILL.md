# KILL — end the session by exact PID

> change 2026-11-07 (review-pilot-cards): step 5 called `taskkill //F //PID`, which is in no source
> file this repo cites for the pilot toolchain. It now retries `um win kill <pid>` (documented,
> exact PID) and keeps the zombie branch; a second failure is the zombie, not an escalation.

GOAL: JC3 is closed, this shell and every other application are untouched, and the PID is on the
record.

Forbidden on this card: `pkill -f <pattern>`, `taskkill /IM <name>`, `Stop-Process -Name`, killing
a window by title. Upstream, `pkill -f` matched the agent's own shell and killed it.

PRE-CONDITIONS
| # | check | command | must show |
|---|---|---|---|
| P1 | the game is running | `um win ps \| grep -i justcause3` | exactly one line |

STEPS

### 1. Read the PID
    DO   um win ps | grep -i justcause3
    SEE  exactly one line; the first column is `<pid>` — write it on the RESULT line
    IF NOT  no line -> nothing to kill, write `RESULT: PASS — already closed` and stop
    IF NOT  two or more lines -> STOP and report; do not kill either

### 2. Kill that PID
    DO   um win kill <pid>
    SEE  exit 0
    IF NOT  non-zero -> go to step 4

### 3. Wait, then confirm it is gone
    DO   sleep 5
    SEE  the next step prints no `JustCause3` line
    IF NOT  re-run this wait once

### 4. Re-list the process
    DO   um win ps | grep -i justcause3
    SEE  no output
    IF NOT  the same `<pid>` is still listed -> step 5

### 5. Retry the same PID once (documented kill only)
    DO   um win kill <pid>
    SEE  exit 0
    IF NOT  non-zero a second time -> the process is a zombie (windowless, one thread, unkillable by PID): STOP, do not relaunch, write `zombie` on the RESULT line
    NOTE  `taskkill //F //PID` was removed on 2026-11-07: it belongs to no source the repo cites for
    this toolchain. Escalating to it would add a command the card cannot justify; the documented
    recovery for a zombie is the reboot, not a stronger kill.

### 6. Confirm the fallback worked
    DO   um win ps | grep -i justcause3
    SEE  no output
    IF NOT  still listed -> STOP: zombie, reboot is the only documented recovery

### 7. Clear a crash reporter, by its own PID
    DO   um win ps | grep -iE "BsSndRpt64|CrashReportClient"
    SEE  no output
    IF NOT  a line is printed -> run step 2 again with **that** PID, then repeat this step

### 8. Confirm this shell survived
    DO   echo ALIVE
    SEE  `ALIVE`
    IF NOT  STOP — something was killed by pattern, which this card forbids

RESULT
    RESULT: PASS — game closed by PID — pid=<pid> — steps 3/4/6 empty
    RESULT: STOP — step <n> — <the SEE that failed, quoted> — pid=<pid>

TRAPS: L-4 (a force-quit can leave an unkillable zombie; no repo evidence, upstream precaution —
the card still checks, and the recovery is a reboot, never a relaunch), name-pattern kills (killed
the agent's own shell upstream), a crashed game's crash reporter blocking the next launch (clear it
by PID, step 7). Assume one launch per boot; after a zombie the next launch is not attempted.
