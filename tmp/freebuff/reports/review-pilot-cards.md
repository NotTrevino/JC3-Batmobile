# Review of the pilot cards (2026-11-07)

STATUS: done — 11 `Working/Q/PILOT` files and the `pilot-*` reports audited against the failure
catalogue and the controls reference. **13 files rewritten in place** (9 cards, 4 card documents),
each with a dated change line;
**7 briefs (86xx) now name the cards they must follow**. Three defect classes found: steps that need
judgement, commands that exist in no source, and observables that cannot be read from a frame.

Measured state used as the frame for the audit: **15 blocked rows** (11 ledger + 4 T6), 109 `next`,
**12 of 23 textures unfaithful**, **21 of 45 audio GUIDs donor** unless B-26, collision **2 bodies /
3 boxes with 2 shapes missing**, and the **3 stale checkers all exit 0** (`v05_driving` 34/34,
`t_boost_rows` 21/21, `t_vnf_six` 87/87).

## 1. What was read, and what was checked

| source | use |
|---|---|
| `Working/Q/PILOT/{CARD_FORMAT,CONTROLS,AIRFIELD,LAUNCH,SCREENSHOT,RECORD,KILL,LOAD_SAVE,SPAWN_BATMOBILE,ENTER_EXIT,PROVE_CARDS}.md` | the 11 card files, read in full and audited |
| `tmp/freebuff/reports/pilot-failure-catalogue.md` | the traps (E-1…E-3, D-1/D-2, C-1…C-3, K-1…K-6, A-1, L-1…L-4, R-1/R-2) each card is checked against |
| `tmp/freebuff/reports/pilot-controls-reference.md` + `Working/Q/PILOT/CONTROLS.md` | every key on a card must be a `decoded` row; `UNKNOWN`/`menu label` rows may not appear as keys |
| `tmp/freebuff/reports/pilot-study-universal-modder.md` | the verbatim WinDrive vocabulary: `launch`, `ps`, `drive`, `shot`, `record`, `kill`, `size`, `click`, `key`, `hold`, `scanmode on`, `idle` |
| `tmp/freebuff/reports/pilot-card-looks-and-audio.md`, `pilot-card-proving-on-a-simple-car.md`, `pilot-card-driving-takes.md`, `pilot-card-combat-and-gadgets.md` | the four card documents outside `Working/Q/PILOT`; audited and fixed |
| `tmp/freebuff/reports/pilot-card-format-and-launch.md` | read for its command-fidelity table (§ lines 38–42) only; it documents no card step — the LAUNCH card itself is `PILOT/LAUNCH.md`, audited in full |

Command fidelity was checked against the WinDrive source, not memory. That found the two worst
command defects (§4). Checkers were re-run for this review:

```
v05_driving.py --check   exit 0   34/34 oracles; ledger 199 rows; D-4 radius 3.52 / 13.82 m; T-ST7 RED
t_boost_rows.py --check  exit 0   21/21 oracles
t_vnf_six.py --check     exit 0   87/87 oracles
status_audit.py --check           STATUS.md is current
```

## 2. The actual state, and what it forbids a card to claim

| fact | measured | consequence carried into the cards |
|---|---|---|
| blocked rows | **15** = 11 in `T_ROWS.jsonl` + 4 in `T6_HUD_CAMERA.md`; ledger also holds `next 109, keep 29, epe 26, edit 16, superseded 7, out 1` | no card may move a blocked row; the combat cards write `BLOCKED` when their batch has not landed |
| textures | **12 of 23 rows unfaithful** (4 chapter masks, 8 pixel sets) | the looks cards record these as known gaps; they do not fail a session |
| audio | **21 of 45 GUIDs donor-carried** unless B-26 | `AUDIO.md` records `donor=21/45`; a donor sample is not a defect |
| collision | **2 bodies / 3 boxes, 2 shapes missing** | a kerb/ram failure in Q-2 is a **B-10 fix card**, not a retune (brief 8602) |
| stale checkers | all three exit 0 and validate a document against its own generator | a green `--check` is **arithmetic**, never test evidence — said at the A3/A4 precondition and in brief 8604 |
| `PROVE_CARDS` | claimed `v05_driving.py --check` "is not green" | **false**; it is green and the RED is the built-vs-goal miss. Fixed |

## 3. Card by card

| card | verdict before | defect(s) found | change |
|---|---|---|---|
| `LAUNCH.md` | strong | step 12 asserted a timing ("returns after about 120 s") no tool reports; no input-layer step, though the source says one down+up `SendInput` "is shorter than a frame" and DirectInput games need `scanmode on` | step 12 checks exit 0 only; **new step 19** sends `scanmode on` once, and later cards retry it before stopping |
| `SCREENSHOT.md` | weak | `<name>` placeholder inside 4 commands (not copy-paste ready, pilot must invent a name); no branch for a key that returns `ok` and changes nothing | literal `shot1`; `scanmode` retry branch |
| `RECORD.md` | strong | the peak reader assumes float32 and had no branch for another encoding — a wrong-format take would have produced a confident number; `--offset 0.25` presented without a label | refuses a peak above 1.0 and names the assumption; offset labelled a **pilot threshold** |
| `KILL.md` | strong | step 5 used `taskkill //F //PID`, which is in no source the repo cites; escalating to an un-sourced command after a failed kill is exactly the pathway to a name kill | replaced by a second documented `um win kill <pid>`; a second failure is the zombie, not an escalation |
| `LOAD_SAVE.md` | strong | step 8 read as unconditional although it only applies when step 7 saw no change — a pilot following the card would click the menu after it had loaded | step 8 conditioned on step 7's `SEE` |
| `SPAWN_BATMOBILE.md` | weak | step 6 told the pilot to read `Bring to garage` / `Err: No Valid locking reason` **off a PNG**; no OCR exists in the repo | machine check is the frame hash; the text becomes `observed (human)` on the RESULT line |
| `ENTER_EXIT.md` | **broken** | (a) step 5 pressed `E` even when `Y` had entered — and `E` is also `EXIT_VEHICLE`, so the card could eject Rico and then score the exit frame as an entry; (b) step 8 copied `enter_y.png` whichever key worked; (c) step 10's heading said `LB` while its command sent `E`, and step 9 appended with `>>`; (d) "CHECK the frame against the expected HUD" was a judgement | step 5 conditioned and explicitly warns off `E`; step 8 names its branch and moves the HUD read to a recorded human observation; step 10 heading matches its command, `LB` is an operator press; step 9 is `>` plus `wc -l` = 1 |
| `AIRFIELD.md` | **broken** | step 7 printed `max()` of the sample deltas, so a positive gain always satisfied `> -5`: **the check could not fail** | `min()`, pass only when no delta is below -5 km/h |
| `PROVE_CARDS.md` | weak | §3 said the driving checker "is not green" (it is); §4 knew only two meanings of B-15 | §3 states the measurement and why green ≠ evidence; §4 lists all three B-15 meanings |
| `pilot-card-looks-and-audio.md` | weak | `HUD_CHECK` step 2 checked `hud_cannon.png`, a file **no step captured**; step 4 wrote the verdict line with the *expected* values already in it (`reticle=8@-111`), i.e. a fabricated measurement; `NIGHT` step 2 required the frame to be "visibly darker"; `AUDIO`'s RESULT named `audio/*.mp4` though nothing muxed one; `close_<target>.png` placeholder | capture added as step 2b; verdict is a template that refuses to be submitted with a `<...>` left; "visibly darker" replaced by a hash plus the reviewer's crop mean; RESULT names the `.mkv` + `.audio.raw` actually written; five literal close-up steps |
| `pilot-card-proving-on-a-simple-car.md` | weak | reported the v05 checker as "started and did not finish in 90 s", implying no status; B-15 row had two meanings | the measurement replaces the timeout; B-15 three meanings |
| `pilot-card-driving-takes.md` | weak | A2 read a `measure` JSON key (`peak_kmh`) that appears in no repo file; A6 could write `PASS` on "ride height unchanged" from two PNGs, which carry no scale; "3 attempts, 2 clean" under-counted brief 8602's "three repeats each"; an "optional" leg made the run order pilot-dependent; §2 did not warn that a green checker is not evidence | CSV arithmetic (the A5 form); ride-height clause deleted, A6 ends `UNKNOWN`; 3 clean takes after one calibration; leg 3 is a step, not an option; stale-checker paragraph added |
| `pilot-card-combat-and-gadgets.md` | weak | §5 mapped C6 (mode switch) to `WPN-11…13`, which is the booster and the slot row, not the mode rows; B-15 named without its path; §6 declared "seven columns" then showed nine | C6 now maps `T-MD5`/`T-MD6`/`T-MD10`/`T-MD11` and the `T-MD8`/`T-MD14` omissions; B-15's three meanings stated; the nine-column combat header is declared as seven + two |
| `CARD_FORMAT.md`, `CONTROLS.md` | strong | none | unchanged |

## 4. The three defect classes, with every instance

**A. A step that needs judgement.**
`SPAWN_BATMOBILE` step 6 (read text off a frame); `ENTER_EXIT` step 8 (judge the HUD) and step 10
(`LB` vs `E`); `HUD_CHECK` step 2 (operator decides whether a cannon is bound); `pilot-card-driving-takes`
A6 (judge ride height from two frames); `LOOK_STATIC` P3 and `NIGHT` P1/P3 (operator states a park/
weather state — kept, but recorded as `operator` on the RESULT line, never scored).

**B. A command not copied from a source.**
`KILL` step 5 `taskkill //F //PID` — replaced. `HUD_CHECK` step 2 pressed LMB in prose with no capture
— replaced by an operator action plus an explicit `um win shot`. `AUDIO` RESULT named `.mp4` files no
step produced — replaced. Everything else was checked against the WinDrive vocabulary and kept:
`launch`, `ps --exe`, `drive --proc` (`key`, `click`, `size`, `scanmode`), `shot --exe --scale`,
`record --pid --seconds --out`, `video mux --offset`, `kill <pid>`, `backup create/list`.

**C. An observable that cannot be checked from a screenshot.**
Text on a menu (`SPAWN_BATMOBILE` step 6), HUD identity (`ENTER_EXIT` step 8), "visibly darker"
(`NIGHT` step 2), ride height (`A6`), radius and drift angle and bounce (already `UNKNOWN` in the two
card documents, with the exact missing tools named). Rule applied: if a PNG has no scale, no OCR and
no gadget that reads the value, the card records the frame and writes `UNKNOWN` for the number.

## 5. What was deliberately not changed

* `CARD_FORMAT.md` and `CONTROLS.md` — the format held; every defect above is a violation of it, not a
  gap in it.
* `LAUNCH` step 1's absolute save path, `KILL`'s PID-only rule, `RECORD`'s no-`--no-audio` rule, and
  every `UNKNOWN` calibration field: all correct and evidence-backed.
* The `Q-1` looks cards' pilot thresholds (2.0–3.0 m, 60/255, ≤12 spread, 8/255, 6 s ±1 s): they are
  labelled as thresholds and calibrated on the first run, which the format permits.
* `pilot-card-format-and-launch.md` — its command table was spot-checked and agreed with the source;
  it carries no card step of its own.

## 6. Briefs 86xx, now naming their cards

| brief | card set it must follow |
|---|---|
| 8600 Q-0 | `PROVE_CARDS.md` §2.1–2.4 + `LAUNCH`, `LOAD_SAVE`, `SCREENSHOT`, `RECORD`, `KILL` |
| 8601 Q-1 | `SCREENSHOT`, `RECORD` + `pilot-card-looks-and-audio.md` (LOOK_STATIC, LOOK_CLOSEUPS, NIGHT, RAIN, HUD_CHECK, AUDIO) |
| 8602 Q-2 | `pilot-card-driving-takes.md` A2, A5, A6, A7, A9 then A1, A3, A4, after `LAUNCH`, `LOAD_SAVE`, `SPAWN_BATMOBILE`, `ENTER_EXIT`, `AIRFIELD`, `RECORD` |
| 8603 Q-3 | `pilot-card-combat-and-gadgets.md` C1–C11, gated per batch (B-15, B-18, B-19, B-20, B-21) |
| 8604 Q-4 | no session card; triage reads `RESULTS.md`; `UNKNOWN` is not a failure and the 3 stale checkers are not evidence |
| 8605 Q-5 | the showcase: driving A2/A7/A9 + combat C1/C3/C7/C6, with unresolved features listed as unbuilt |
| 8699 final review | every `PILOT` card + the three card documents; `UNKNOWN` never counts as a pass |

## 7. Checks run, and revert

| # | check | result |
|---|---|---|
| 1 | change lines found across `Working/Q/PILOT/*.md` and `tmp/freebuff/reports/pilot-card-*.md` | **13 files rewritten**: 11 carry a `> change 2026-11-07` block (`AIRFIELD`, `LAUNCH`, `SCREENSHOT`, `RECORD`, `KILL`, `LOAD_SAVE`, `SPAWN_BATMOBILE`, `ENTER_EXIT`, `PROVE_CARDS`, `pilot-card-looks-and-audio`, `pilot-card-proving-on-a-simple-car`); the two card documents (`pilot-card-driving-takes`, `pilot-card-combat-and-gadgets`) carry the same date as a bold sentence under their title |
| 2 | `grep -c "CARDS (2026-11-07)" tmp/freebuff/queue/86*.txt` | 1 in each of the 7 briefs |
| 3 | checkers re-run | all exit 0 (34/34, 21/21, 87/87) |
| 4 | ledger counted | 199 rows, 11 blocked (+4 T6 = 15), 109 next |
| 5 | no key outside `CONTROLS.md`'s `decoded` rows appears as a key | `E 0x45`, `W 0x57`, `S 0x53`, `Esc 0x1B` only; `B` never pressed; `LB` recorded as an operator press |
| 6 | no game process started, no install, no save written | true — read-only audit plus file edits |

**Revert:** each rewritten file's `> change 2026-11-07 (review-pilot-cards)` block names its edit;
deleting the block restores the card's previous text. The brief lines are one appended line per file
(`CARDS (2026-11-07): …`) and are removed by deleting that line. This report is deleted on its own.
