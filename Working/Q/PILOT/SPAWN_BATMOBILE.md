# SPAWN_BATMOBILE — make the Batmobile arrive (console route, Rebel Drop fallback)

> change 2026-11-07 (review-pilot-cards): step 6 told the pilot to read `Bring to garage` or
> `Err: No Valid locking reason` off a PNG. No OCR exists in this repo, so that observable is not
> machine-checkable — it is now a recorded human read, and the machine check is the frame hash.
>
> change 2026-11-08 (wheel-check P3/P4, `pilot-cards-wheel-check.md` §3): **the primary route is now
> the console** (`jc3-console-thingy`, MIT, `spawn <name>`), because a name-typed spawn deletes the
> three `UNKNOWN` menu-calibration fields. The Rebel Drop route is kept whole as **Route B** and
> `OPEN_DROP` / `DROP_ENTRY_CLICK` / `CONFIRM_CLICK` are now *fallback-only* fields — a calibration
> value that is only needed on a fallback is not a blocker. The E-3 trap ("listed ≠ spawnable") is
> unchanged: the console removes the list, not the trap.

GOAL: the Batmobile is in front of the player and the frame proves it, by the console if the console
works, by Rebel Drop if it does not.

## ROUTES

| route | how | needs | status |
|---|---|---|---|
| **A (primary)** | `spawn <hint>` in the console | `xinput9_1_0.dll` installed through `CONSOLE_RECEIPT.md`; the hint string | preferred: no menu, no beacon, no restock |
| **B (fallback)** | Rebel Drop list, entry `BATMOBILE` | `OPEN_DROP`, `DROP_ENTRY_CLICK`, `CONFIRM_CLICK` calibration | proven once (MODLOG Q-1a re-test 3); the only route with a recorded PASS |

Do not mix: a take uses A or B, and the RESULT line names which.

WHAT `bm_rebel.py` BUILT (the offline half of this card; every value is from that script)
`Tools/scripts/bm_rebel.py` writes one `Item` into `profile/item.onlinec`, one `ItemReward` into
`profile/task.onlinec`, two string-hash pairs per language into `profile/online.stringlookup`, one
icon, and one record in `settings/spawn_vehicle_defs.bin`:

| built field | value | why that value (as recorded in the script) |
|---|---|---|
| `Name`, `UIName` | `hash(leaf)` = 443190071 | vanilla convention: `UIName == Name == hash(leaf)` |
| `UIDescription` | `hash(leaf + "_desc")` | vanilla donor follows the same `_desc` pair |
| `UIDisplayOrder` | `12` | `jc3rebeldrop` recipe, `free_order` = max + 1 |
| `UIFlag`, `UIFlagDescription` | `7`, `1492769243` | vanilla group 7 = armouredjeep / armouredtransport / technicaljeep / buggy rebel — operator: "military, not sports" (2026-11-02) |
| `UIImagePath` | the new leaf; `.ddsc` byte-copied from the donor icon | `T-WLD5` |
| `UIVideoPath` | donor string kept | no video asset exists for the leaf (UNKNOWN in the UI) |
| unlock | `+1 ItemReward (leaf, 1, 0, 1, 0)` on the **repeatable** reward of task `1980624442` (type 100, vanilla's starter grant) | the donor-task gate left the entry LOCKED on a passed save; no reward gave "Err: No Valid locking reason" |
| spawn record | donor record cloned for the leaf: `tags = vehicle,batmobile`, `select 1`, `debug vehicle\|ground\|rebel`, entity = the build's `.ee` | the donor's `Name` hash occurs in exactly 3 files: `item.onlinec`, `task.onlinec`, `spawn_vehicle_defs.bin` |

THE SCREENS THIS DROP HAS ACTUALLY SHOWED (each with its literal text and its source)

| # | screen / state | what it shows | source |
|---|---|---|---|
| 1 | main menu | `UNKNOWN` — no file records JC3's main-menu labels | repo-wide grep, 2026-11-06 |
| 2 | Rebel Drop list, entry present | the row labelled **BATMOBILE**, donor icon, in the military/armour group | `MODLOG.md` "Q-1a (user): entry \"BATMOBILE\" present in Rebel Drop -> PASS"; `NAMES.md` (the name resolves through `profile/online.stringlookup`) |
| 3 | entry **LOCKED** (historical, build before B-13a) | `Bring to garage` — the lock reason of the donor's type-19 task `1361701860` | `MODLOG.md` 2026-11-02 Q-1a |
| 4 | entry with **no reward** (historical) | `Err: No Valid locking reason` | `MODLOG.md` Q-1a re-test 2 |
| 5 | entry selected, **nothing arrives** (historical) | empty drop — no `spawn_vehicle_defs.bin` record for the leaf | `MODLOG.md` Q-1a re-test 2 / probe 2; B-13c |
| 6 | entry selected, **car delivered** | the car drops in front of the player | `MODLOG.md` Q-1a re-test 3 (B-13c PASS, screenshot `Captures/Just Cause 3 11_2_2026 4_42_02 AM.png`) |

Screens 3-5 are the failure states Route B's `IF NOT` lines point at. The **navigation** from screen 1
to screen 2 (which menu, which key) is `UNKNOWN` in this repo — that is why Route A exists and why
Route B still carries calibration fields instead of a guessed menu path.

## ROUTE A — console (`jc3-console-thingy`)

Evidence: https://github.com/aaronkirkham/jc3-console-thingy (MIT). Install: drop
`xinput9_1_0.dll` in the JC3 folder, open with `~` or `F1`; commands `spawn`, `event`, `world`.
DLL version, sha256, staging path and undo: **`Working/Q/PILOT/CONSOLE_RECEIPT.md`** — the card never
installs it.

The string: `spawn` takes a **model name** (decoded from `src/commands/spawn.h` +
`src/game/spawn_system.h`: the argument string is forwarded as `model_name.c_str()` to the native at
`0x140E97DA0`; names come from the property-file entry `0xF71C2A21`). The Batmobile's leaf is
`v0300_car_kensington_sportsmuscle_debug`; whether that string is in the name table is **UNKNOWN**
(no source shows the console spawning a mod entity) — the console's own hint list is the oracle.

CALIBRATION (Route A, fill once on the first run)
    CONSOLE_OPEN=<the key that opened the console: `~` or `F1`, as observed>
    BATMOBILE_HINT=<the hint the console listed for v0300_car_kensington_sportsmuscle_debug>
    CONSOLE_TYPE=<the WinDrive command that typed the text, or `manual` if typing is refused>

A1. Pre-check the DLL is installed (read-only)
    DO   ls -l "D:\Games\Just Cause 3\xinput9_1_0.dll"
    SEE  one line whose sha256 matches `CONSOLE_RECEIPT.md` (`sha256sum "D:/Games/Just Cause 3/xinput9_1_0.dll"`)
    IF NOT  absent or a different hash -> **Route A is unavailable: go to B1** (the card does not install it)

A2. Capture the screen before
    DO   um win shot --exe JustCause3.exe Working/Q/PILOT/shots/drop_00.png
    SEE  the file exists, larger than 0 bytes
    IF NOT  STOP — capture dead, run SCREENSHOT step 7

A3. Open the console
    DO   um win drive --proc JustCause3 "key 0xC0"
    SEE  `ok`
    IF NOT  `fail` -> STOP, the game is not foreground
    NOTE  `~` is 0xC0; F1 is 0x70. Which one JC3 binds is recorded in `CONSOLE_OPEN` on success.
    The console is visible as a frame change in A4; if neither key changes the frame, Route A is
    unavailable -> go to B1.

A4. Prove the console opened
    DO   um win shot --exe JustCause3.exe Working/Q/PILOT/shots/drop_01.png
    SEE  sha256 differs from `drop_00.png`
    IF NOT  identical -> close with the same key, go to B1 (record `console=no-ui`)

A5. Spawn the Batmobile by name
    DO   um win drive --proc JustCause3 "<CONSOLE_TYPE: spawn <BATMOBILE_HINT>>"
    SEE  `ok`
    IF NOT  `fail` or `manual` -> the operator types it once and the take is recorded as
    `ACCEPTANCE: not met — console typing needed`; then continue at A6 (the frame still decides)
    NOTE  the spawn places the entity at the crosshair, 1.0 m up (spawn.h replaces the transform
    translation with `m_aimPos`). Look where Rico is aiming, not at the ground.

A6. Close the console and capture the car
    DO   um win drive --proc JustCause3 "key 0xC0" ; sleep 2 ; um win shot --exe JustCause3.exe Working/Q/PILOT/shots/drop_03.png
    SEE  `drop_03.png` exists and differs from `drop_02.png` (the pre-close frame) / `drop_01.png`
    IF NOT  identical -> nothing spawned: if the hint list had no Batmobile entry, record
    `hint=absent` (U3 = no) and go to B1; if the hint was there, STOP — the payload did not reach
    the name table

A7. Process and dump check
    DO   ls -t "$LOCALAPPDATA/CrashDumps" | grep -i justcause3 | head -1
    SEE  no output
    IF NOT  a dump name -> STOP with it on the RESULT line. **Attribute it:** a crash here can be the
    console DLL, not the payload (a second in-process hook beside the dropzone). Re-run the take
    without the DLL (remove it per the receipt) before blaming the build.

## ROUTE B — Rebel Drop (fallback)

CALIBRATION (fallback only — needed if A1/A4/A6 sends the take here)
    OPEN_DROP=<commands that open the Rebel Drop list from free roam>
    DROP_ENTRY_CLICK=<x y inside the client area of the BATMOBILE row>
    CONFIRM_CLICK=<x y that confirms the drop>

PRE-CONDITIONS (both routes)
| # | check | command | must show |
|---|---|---|---|
| P1 | LOAD_SAVE PASS | `Working/Q/PILOT/LOAD_SAVE.md` | `RESULT: PASS` |
| P2 | the entry exists in the built tables | `python Tools/scripts/bm_rebel.py --check` | `PASS: B-13 0 failure(s)` |
| P3 | a route is usable | `ls -l "D:\Games\Just Cause 3\xinput9_1_0.dll"` (Route A) **or** `grep -E "^    (OPEN_DROP\|DROP_ENTRY_CLICK\|CONFIRM_CLICK)=<" Working/Q/PILOT/SPAWN_BATMOBILE.md` (Route B) | A: the receipt's sha256; B: no output (the three placeholders are gone). **At least one route must pass** — if neither does, STOP at step 0 |

B0. Prove the item table offline
    DO   python Tools/scripts/bm_rebel.py --check
    SEE  `PASS: B-13 0 failure(s)` and the line `item.onlinec decodes: 196 -> 197 items, 1 Batmobile`
    IF NOT  `FAIL: B-13` -> STOP: the installed build and the receipt disagree; not a pilot fault

B1. Capture the screen before opening the drop
    DO   um win shot --exe JustCause3.exe Working/Q/PILOT/shots/drop_00.png
    SEE  the file exists, larger than 0 bytes
    IF NOT  STOP — capture dead, run SCREENSHOT step 7

B2. Open the Rebel Drop list
    DO   um win drive --proc JustCause3 "<OPEN_DROP>"
    SEE  `ok`
    IF NOT  `fail` -> STOP, the game is not foreground

B3. Confirm the list opened
    DO   um win shot --exe JustCause3.exe Working/Q/PILOT/shots/drop_01.png
    SEE  sha256 differs from `drop_00.png`
    IF NOT  identical -> STOP: the drop did not open; the calibration for P3 is wrong

B4. Select the BATMOBILE row
    DO   um win drive --proc JustCause3 "click <DROP_ENTRY_CLICK>"
    SEE  `ok`
    IF NOT  `fail` -> STOP

B5. Capture the selected state
    DO   um win shot --exe JustCause3.exe Working/Q/PILOT/shots/drop_02.png
    SEE  the file exists and differs from `drop_01.png`
    IF NOT  identical -> the click missed the row: repeat B4 once, then STOP
    NOTE  whether the frame carries `Bring to garage` or `Err: No Valid locking reason` is a HUMAN read
    (the repo has no OCR for a PNG); record it on the RESULT line as `observed (human): <text>`, and do
    not claim the card detected it. The machine check for this step is only the hash difference above.

B6. Confirm the drop
    DO   um win drive --proc JustCause3 "click <CONFIRM_CLICK>"
    SEE  `ok`
    IF NOT  `fail` -> STOP

B7. Wait for the delivery
    DO   sleep 10
    SEE  the command returns, exit 0
    IF NOT  re-run once

B8. Capture the delivered car
    DO   um win shot --exe JustCause3.exe Working/Q/PILOT/shots/drop_03.png
    SEE  the file exists and differs from `drop_02.png`
    IF NOT  identical -> screen 5 (empty drop): STOP and say so on the RESULT line

B9. Confirm the process and the dump folder
    DO   ls -t "$LOCALAPPDATA/CrashDumps" | grep -i justcause3 | head -1
    SEE  no output
    IF NOT  a dump name -> STOP with it on the RESULT line

RESULT
    RESULT: PASS — BATMOBILE delivered — route=A|B — pid=<pid> — shots/drop_00..03.png
    RESULT: STOP — step <n> — <the SEE that failed, quoted> — <artifacts so far>

TRAPS: E-3 (a listed vehicle is not spawnable — the `spawn_vehicle_defs.bin` record is the missing
link, that is what B-13c added; a new leaf also does not load, so the card never proposes one). The
LOCKED / "No Valid locking reason" screens are real observed states, not hypotheticals. Route A has
its own traps: the tool is from 2018 and untested against this 2025-12-17 build (**UNKNOWN**), the
DLL is a second in-process hook (crash attribution, see A7), and a custom `.ee` may be absent from
the name table (**UNKNOWN** — U3). Navigation keys on Route B are UNKNOWN by design: the card
carries calibration fields instead of inventing a menu path.
