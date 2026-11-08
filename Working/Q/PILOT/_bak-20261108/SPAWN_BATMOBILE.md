# SPAWN_BATMOBILE — make the Batmobile arrive by Rebel Drop

> change 2026-11-07 (review-pilot-cards): step 6 told the pilot to read `Bring to garage` or
> `Err: No Valid locking reason` off a PNG. No OCR exists in this repo, so that observable is not
> machine-checkable — it is now a recorded human read, and the machine check is the frame hash.

GOAL: the Rebel Drop entry named **BATMOBILE** is selected and the car is delivered in front of the
player.

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

Screens 3-5 are the failure states this card's `IF NOT` lines point at. The **navigation** from
screen 1 to screen 2 (which menu, which key) is `UNKNOWN` in this repo — no file records it, so it
is a calibration field, never a guess.

CALIBRATION (fill on the first run)
    OPEN_DROP=<commands that open the Rebel Drop list from free roam>
    DROP_ENTRY_CLICK=<x y inside the client area of the BATMOBILE row>
    CONFIRM_CLICK=<x y that confirms the drop>

PRE-CONDITIONS
| # | check | command | must show |
|---|---|---|---|
| P1 | LOAD_SAVE PASS | `Working/Q/PILOT/LOAD_SAVE.md` | `RESULT: PASS` |
| P2 | the entry exists in the built tables | `python Tools/scripts/bm_rebel.py --check` | `PASS: B-13 0 failure(s)` |
| P3 | calibration done | `grep -E "^    (OPEN_DROP|DROP_ENTRY_CLICK|CONFIRM_CLICK)=<" Working/Q/PILOT/SPAWN_BATMOBILE.md` | no output (the placeholders are gone) |

STEPS

### 1. Prove the item table offline
    DO   python Tools/scripts/bm_rebel.py --check
    SEE  `PASS: B-13 0 failure(s)` and the line `item.onlinec decodes: 196 -> 197 items, 1 Batmobile`
    IF NOT  `FAIL: B-13` -> STOP: the installed build and the receipt disagree; not a pilot fault

### 2. Capture the screen before opening the drop
    DO   um win shot --exe JustCause3.exe Working/Q/PILOT/shots/drop_00.png
    SEE  the file exists, larger than 0 bytes
    IF NOT  STOP — capture dead, run SCREENSHOT step 7

### 3. Open the Rebel Drop list
    DO   um win drive --proc JustCause3 "<OPEN_DROP>"
    SEE  `ok`
    IF NOT  `fail` -> STOP, the game is not foreground

### 4. Confirm the list opened
    DO   um win shot --exe JustCause3.exe Working/Q/PILOT/shots/drop_01.png
    SEE  sha256 differs from `drop_00.png`
    IF NOT  identical -> STOP: the drop did not open; the calibration for P3 is wrong

### 5. Select the BATMOBILE row
    DO   um win drive --proc JustCause3 "click <DROP_ENTRY_CLICK>"
    SEE  `ok`
    IF NOT  `fail` -> STOP

### 6. Capture the selected state
    DO   um win shot --exe JustCause3.exe Working/Q/PILOT/shots/drop_02.png
    SEE  the file exists and differs from `drop_01.png`
    IF NOT  identical -> the click missed the row: repeat 5 once, then STOP
    NOTE  whether the frame carries `Bring to garage` or `Err: No Valid locking reason` is a HUMAN read
    (the repo has no OCR for a PNG); record it on the RESULT line as `observed (human): <text>`, and do
    not claim the card detected it. The machine check for this step is only the hash difference above.

### 7. Confirm the drop
    DO   um win drive --proc JustCause3 "click <CONFIRM_CLICK>"
    SEE  `ok`
    IF NOT  `fail` -> STOP

### 8. Wait for the delivery
    DO   sleep 10
    SEE  the command returns, exit 0
    IF NOT  re-run once

### 9. Capture the delivered car
    DO   um win shot --exe JustCause3.exe Working/Q/PILOT/shots/drop_03.png
    SEE  the file exists and differs from `drop_02.png`
    IF NOT  identical -> screen 5 (empty drop): STOP and say so on the RESULT line

### 10. Confirm the process and the dump folder
    DO   ls -t "$LOCALAPPDATA/CrashDumps" | grep -i justcause3 | head -1
    SEE  no output
    IF NOT  a dump name -> STOP with it on the RESULT line

RESULT
    RESULT: PASS — BATMOBILE delivered — pid=<pid> — shots/drop_00..03.png
    RESULT: STOP — step <n> — <the SEE that failed, quoted> — <artifacts so far>

TRAPS: E-3 (a listed vehicle is not spawnable — the `spawn_vehicle_defs.bin` record is the missing
link, that is what B-13c added; a new leaf also does not load, so the card never proposes one), the
LOCKED / "No Valid locking reason" screens are real observed states, not hypotheticals. Navigation
keys are UNKNOWN by design: the card carries calibration fields instead of inventing a menu path.
