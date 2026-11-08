STATUS: done. Format + four cards written; nothing was launched, installed, captured or killed
(the test ban stands: `tmp/freebuff/APPROVED_Q.txt` does not exist). One check could not be
completed and is reported as such in §5.

# Q-PILOT step 4 — card format and the first four cards

Deliverables (all in this repo):

| file | what it is |
|---|---|
| `Working/Q/PILOT/CARD_FORMAT.md` | the page shape, the author rules, the result-line grammar, the card index |
| `Working/Q/PILOT/LAUNCH.md` | saves snapshot → installer green → 1600x900 window → main menu, 18 steps |
| `Working/Q/PILOT/SCREENSHOT.md` | one frame on disk + proof the capture oracle is live, 9 steps |
| `Working/Q/PILOT/RECORD.md` | 20 s take with the game's own audio, proven non-silent, 7 steps |
| `Working/Q/PILOT/KILL.md` | end the session by exact PID, 8 steps |

## 1. The format, in one line

Every card is `GOAL` · `PRE-CONDITIONS` (command + must-show) · numbered `STEPS` where each step
is exactly `DO` (one copy-pasteable command) / `SEE` (a machine comparison: exit code, literal
string the tool prints, file exists, byte size, two hashes equal or different) / `IF NOT` (a step
number or `STOP` + why) · one `RESULT` line, `PASS` or `STOP`, carrying the PID and the artifacts.
No step asks the pilot to judge anything, and no `IF NOT` is open-ended: it names a step or stops.

Eleven author rules are written down; the ones that change behaviour are: one action per line;
`SEE` strings are quoted from a tool, not remembered; three identical failures = STOP (the oracle
note's circuit breaker); keys only from `CONTROLS.md` rows labelled `decoded`; an invented
threshold is labelled a pilot threshold and calibrated on the first run; PID only, never a name
pattern; no install/restart/reboot inside a card; a card is never edited mid-session.

## 2. Where every command came from

Nothing was invented. Each command was traced to a file in this repo or to the tool's own `--help`
output read today:

| command used in a card | evidence |
|---|---|
| `um backup create "<dir>" --name jc3-saves` | `um backup --help` (read this session); the same snapshot name and dir appear in `um backup list`: `jc3-saves 20261031-210237.zip 50 files C:\Users\User\Documents\Square Enix\Just Cause 3` |
| `um win ps` / `kill <pid>` / `shot --exe` / `drive --proc` / `record` / `launch` | `um win --help` and each subcommand's `--help`, read this session; flags `--scale`, `--pid`, `--seconds`, `--out`, `--crop`, `--offset` confirmed there |
| `size 1600 900` | `um win drive` accepts WinDrive commands; `size <w> <h>` sets the client size (pilot-study report §1) |
| VFS launch line | `JC3_Launcher.bat`: `start "" "JustCause3.exe" --vfs-fs dropzone --vfs-archive patch_win64 --vfs-archive archives_win64 --vfs-archive dlc_win64 --vfs-fs .` — reproduced through `um win launch` instead of `start` so the card gets an exit code |
| `pwsh Working/Installer/install_v3.ps1 -Action Verify -GameDir 'E:\Modding\_dropzone_sim_rc2_v3'` | `Tools/scripts/install_v3.py` header + body: `Verify` prints `ok <rel>` / `BAD <rel>` then `verified <n>/<N>`, exits 1 on any `BAD`; `-GameDir` must be the sim root or below, and real game roots (`D:\Games`, `E:\Games`) are refused |
| `python Tools/scripts/install_v3.py --check` → `CHECK_EXIT=0` | `install_v3.py:730-737` prints `FAIL: <name>` + `CHECK_EXIT=1`, else `PASS: ...` + `CHECK_EXIT=0` |
| `pwsh -File Builds/bm-RC2/install.ps1 -Action Verify -GameDir 'D:\Games\Just Cause 3'` | `Builds/bm-RC2/install.ps1` param block (default `-GameDir 'D:\Games\Just Cause 3'`) and its `Verify` branch: same `ok`/`BAD` + `verified n/9` output |
| `Esc` = `0x1B` for the liveness check | `CONTROLS.md` row 23, JC3 `GUI_PAUSE = START / ESCAPE`, labelled `decoded` |

Receipt row count is 9 (`Builds/bm-RC2/install.ps1` lists 9 targets; `install_v3.py` notes
"Install snapshots 9/9"), so both Verify steps require the literal `verified 9/9`.

## 3. The traps each card defends against

`LAUNCH` — L-1 (the first QA-1 recording died with the game before the menu, so launch and record
are separate cards and `LAUNCH` must reach a menu before `RECORD` may run); L-2 (a new dump is
found by name and stops the card instead of being blamed on the build); L-4 (one launch per boot;
no force-quit inside this card); K-1 (no key is pressed at all here, so no binding is claimed).
`SCREENSHOT` — the frozen-oracle trap, made testable: `Esc` opens the pause overlay, so a hash
that does not change proves the capture is dead and every frame from the session is unusable.
`RECORD` — A-1, the QA-1 lesson: `--no-audio` deleted JC3's only rpm channel, so audio is treated
as a data channel and the take is only accepted when the measured peak is above 0.001 (a per-app
mute yields exact silence). `KILL` — exact PID, the documented zombie check, and crash reporters
cleared by their own PID.

Honest labelling: focus-lost, window-not-found and zombie have **no repo evidence** (catalogue
L-3/L-4). They appear as bounded checks with the upstream source named, never as lessons learned
here.

## 4. Deliberate omissions

* The first four cards are the ones the format needs to be proven on; `LOAD`, `SPAWN`, `ENTER`,
  `DRIVE`, `FIGHT` are listed in `CARD_FORMAT.md` §4 as **not written**, with the traps they must
  carry. They are the next step of Q-PILOT, not part of this card.
* No binding is claimed for boost, mode switch, tracker, EMP, barrage, eject, sonar or winch: all
  are `UNKNOWN` in `CONTROLS.md` §2 and appear in no card as a key. That is the K-2 lesson
  (5/5 operator statements were UNKNOWN from the script) applied to the cards themselves.
* No windowed **launch flag** for JC3 exists in this repo; the card sets the size through WinDrive
  and simply records the captured frame size. It requires a *stable* size across three captures
  rather than asserting an exact 1600x900, because the capture may include the window border.
* The 100 kB/0.001/0.25 numbers are pilot thresholds (0.25 s is the upstream-measured encoder
  offset), flagged as such where they appear.

## 5. Checks run, and the one that did not finish

Read-only / offline, run this session:
`um --help`, `um win --help`, `um win drive|shot|record|kill|launch --help`,
`um backup --help`, `um scan --help`, `um backup list` (three snapshots listed; `jc3-saves`
confirmed against the real save folder), `um win ps` (game absent), `pwsh -v` → 7.5.5,
`ls -d E:/Modding/_dropzone_sim_rc2_v3*` → the sim root and `..._v3_prefix_4020` exist.

**Not completed:** `python Tools/scripts/install_v3.py --check` was started and **timed out at
240 s** without reaching its final line. It did create `E:\Modding\_dropzone_sim_rc2_v3` and
`E:\Modding\_dropzone_sim_rc2_v3_prefix_4020` before being cut off, so that state is partial. This
is why `LAUNCH.md` step 3 says "allow up to 10 minutes" and requires the literal `CHECK_EXIT=0`
rather than reporting the check as green: **the installer self-check has not been observed passing
in this session.** The `SEE` strings in steps 3–5 are quoted from the scripts' source, not from a
completed run.

Also not done, by scope: no DeepSeek read-through (the card's own `Done` criterion — it needs the
model lane and is the cheap next test), and no game action of any kind.

## 6. Revert

Delete `Working/Q/PILOT/{CARD_FORMAT,LAUNCH,SCREENSHOT,RECORD,KILL}.md`; remove the MODLOG section
that records them. `CONTROLS.md` and every other existing file are untouched.
