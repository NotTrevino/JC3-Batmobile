# Piloting card format (Q-PILOT step 4)

Purpose: a small model (DeepSeek) must be able to drive JC3 by reading one page and executing
it, with no judgement calls and no invented keys. A **card is one numbered page for one action**.
If a card needs the pilot to decide something, the card is wrong — fix the card, never the pilot.

Sources for every command in a card (do not add commands from memory):
`tmp/freebuff/reports/pilot-study-universal-modder.md` (the um/universal-modder commands),
`tmp/freebuff/reports/pilot-controls-reference.md` + `Working/Q/PILOT/CONTROLS.md` (keys),
`tmp/freebuff/reports/pilot-failure-catalogue.md` (the traps). A card that needs a command or a
key not in those three files is blocked, not guessed.

## 1. The page

Every card is exactly this shape, in this order, and fits one screen:

```
# <ID> — <one-line action>

GOAL: <what is true after a PASS, one sentence, no adjectives>

PRE-CONDITIONS (all must hold before step 1)
| # | check | command | must show |
|---|---|---|---|
| P1 | ... | `...` | ... |

STEPS
### 1. <imperative verb + object>
    DO   <one command, one line, copy-paste ready>
    SEE  <exact stdout string | exit code | file property | number range>
    IF NOT  <step N to run next, or STOP + why>

### 2. ...

RESULT
    RESULT: PASS — <one clause> — pid=<pid> — <artifact paths>
    RESULT: STOP — step <n> — <exact observation> — <artifact paths>

TRAPS: <ids from the failure catalogue this card defends against>
```

Five required fields, nothing else: **goal, preconditions, exact commands, a checkable
observation after each step, what to do when it is not met** — plus the result line.

## 2. Rules for the author

1. **One action per numbered line.** Two commands that must both run = two steps.
2. **`SEE` is a machine comparison**, not an opinion: an exit code, a literal string the tool
   prints, a file that exists, a byte size, a number in a range, two hashes equal/different.
   Banned: "looks right", "appears", "correct", "the car drives well", "the menu is fine".
3. **`SEE` strings are copied from the tool**, not remembered. `CHECK_EXIT=0`, `verified 9/9`,
   `ok <path>`, `REFUSED:`, `ok|fail` are quoted from the source or from a run in this repo.
4. **`IF NOT` names a step number or `STOP`.** Every `IF NOT` ends in a bounded loop (max 2
   retries) or `STOP`; never "try a few things".
5. **Three identical failures = STOP.** Write the observation on the RESULT line and change
   approach. This is the circuit breaker from the oracle note, and it is not optional.
6. **Keys come from `CONTROLS.md` only.** A row labelled `UNKNOWN` may not appear in a card as a
   key. Cards use only `decoded` rows; a `menu label` row is named as a label, never as a key.
7. **A threshold invented for the card is labelled a pilot threshold** and calibrated on the
   first run; the calibrated number is written into the card. A threshold is never presented as a
   decoded value.
8. **PID only.** Every card that touches a process reads the PID from `um win ps` and writes it on
   its RESULT line. `pkill -f`, `taskkill /IM`, and any name pattern are forbidden (they killed
   the agent's own shell upstream).
9. **No install, no restart, no reboot inside a card.** Those are build/operator actions; a card
   that needs one STOPs and says so.
10. **A card is not edited mid-session.** If it is wrong, STOP; the fix is written after the
    session, with the observation that forced it.
11. **One launch per boot** (upstream zombie trap; no repo evidence — precaution, not a lesson).
    So `LAUNCH` is the only card that starts the game, and `KILL` is the only card that ends it.
12. **Recording is with audio.** `--no-audio` is banned: it deleted JC3's only rpm channel in
    QA-1 (§1.5, A-1).

## 3. Result line grammar

One line, three parts, separated by ` — `:

* `RESULT: PASS — <what is now true> — pid=<pid> — <files produced>`
* `RESULT: STOP — step <n> — <the SEE that failed, quoted> — <files produced so far>`

The line is the handover to the next card and the MODLOG entry. A card with no RESULT line did
not run.

## 4. The cards

| card | action | state | traps it defends |
|---|---|---|---|
| `LAUNCH.md` | saves backed up, installer verified, game windowed at 1600x900, main menu reached | written (step 4) | L-1 launch≠record, L-2 dump signature, L-4 zombie (precaution), K-1 no invented keys |
| `SCREENSHOT.md` | one frame on disk plus proof the oracle is live | written (step 4) | frozen oracle (`oracles` note), R-1/R-2 readout |
| `RECORD.md` | 20 s take with the game's own audio, proven non-silent | written (step 4) | A-1 `--no-audio`, per-app mute (silence) |
| `KILL.md` | end the session by exact PID | written (step 4) | L-4 zombie (precaution), name-pattern kills |
| `LOAD_SAVE.md` | from the main menu into free roam on profile `76561197960271872` | written (step 5) | L-2 dump, A-1 save backup, no invented menu key (calibration fields) |
| `SPAWN_BATMOBILE.md` | Rebel Drop entry "BATMOBILE" selected, car delivered | written (step 5) | E-3 listed≠spawnable, LOCKED / "No Valid locking reason" screens |
| `ENTER_EXIT.md` | enter with `Y` (fallback `E`), camera/HUD frame, exit `LB` (fallback `E`) | written (step 5) | E-1/E-2 entry volume, K-1/K-2 stated binding, conflict A/B |
| `AIRFIELD.md` | prove the straight test strip from the trace | written (step 5) | D-1/D-2 free-run off the road, A-1 audio |
| `DRIVE.md` | one prescribed manoeuvre per take | not written | D-1/D-2 free-run off the road |
| `FIGHT.md` | one weapon, one target | not written | K-2..K-5 binding/lock traps |

`DRIVE.md` and `FIGHT.md` are the remaining Q-PILOT cards; they follow §1–§3 unchanged and none of
them may claim a binding that `CONTROLS.md` marks `UNKNOWN`.

### 4a. Calibration fields (the one legal way to handle an UNKNOWN)

Where the repo has no evidence for a *navigation* fact (a menu key, a click point, a location),
a card carries a **calibration field** with `UNKNOWN` as its value, and its pre-conditions refuse to
run until the field holds a value. The first run of that card is a calibration run: the operator
performs the action once and writes the key/click/location into the card. This is the only
permitted alternative to `STOP`, and it never lets a model guess a binding. Cards that use it:
`LOAD_SAVE.md` (`ENTER_KEY`, `SAVE_SLOT_CLICK`), `SPAWN_BATMOBILE.md` (`OPEN_DROP`,
`DROP_ENTRY_CLICK`, `CONFIRM_CLICK`), `AIRFIELD.md` (`STRIP_START`, the two reference shots,
`STRIP_LENGTH_M`).
