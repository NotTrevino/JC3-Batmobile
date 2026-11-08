# Operator digest — pilot cards, status at 2026-11-07

One page. Sources are the four card documents plus the review, all in `tmp/freebuff/reports/`.
Counts are **copied** where the file states an aggregate; where it does not, the row says which
table was counted. Nothing here was executed: every `SEE` in these files is a file property or a
command's own print, not an observation of the game.

## 1. Cards per area — 34 in total

| area | file | cards | where the number comes from |
|---|---|---:|---|
| Q-2 driving takes | `pilot-card-driving-takes.md` | **8** | §1 table (`GRAB_BACKLOG.md` §9b order) names A2, A5, A6, A7, A9, A1, A3, A4; §5.1–§5.8 is eight headed cards; §6's verdict table has eight rows |
| Q-3 combat & gadgets | `pilot-card-combat-and-gadgets.md` | **11** | line 3: *"Eleven cards: cannon, Vulcan, lock-on missiles, EMP, riot mode, mode switch, afterburner, sonar, winch, hacker, tracker"*; §4.1–§4.11; §5 rows C1–C11 |
| Q-1 looks & audio | `pilot-card-looks-and-audio.md` | **6** | line 13: *"Six cards … `LOOK_STATIC.md` … `LOOK_CLOSEUPS.md` … `NIGHT.md`, `RAIN.md`, `HUD_CHECK.md`, `AUDIO.md`"* |
| Prove-set on a stock Serpente | `pilot-card-proving-on-a-simple-car.md` | **9** | §2: *"Nine cards, run in this order, one at a time"* — P1–P9; *"Five existing cards … Four are new"* |

## 2. Numeric pass band — 18 of the 34

Definition used (and the only one that survives the files): the card's **own** expected value is a
number or bounded range it can fail against. A card that passes on a file existing or a hash
differing, with no number in its verdict, is not counted.

| area | numeric band | cards, with the file's own wording |
|---|---:|---|
| Driving | **8 of 8** | every card has a `number | band | source` table in §5: A2 240–294 km/h and +32.4…+43.2; A5 101.5–110.2 m; A6 0.70 m and ≤1 rebound; A7 20°/45°, ~2 s, 0.3 s, 0.625; A9 **pilot band** 4.5–7.5 m/s²; A1 15.6–17.2 s; A3 3.17–3.87 / 12.44–15.20 m; A4 0.25 s / 0.091 s |
| Combat | **7 of 11** | C1 2–3 hits (§4.1); C3 4 missiles (§4.3); C5 0.75 s and 5 hits (§4.5); C6 threshold "**0.05 or 0.2**" (§4.6); C7 +32.4…+43.2 km/h (§4.7); C10 cooldown **1 s** (§4.10); C11 **30.0 deg** up (§4.11). Excluded: C2 (its 30 s is *"the probe length, not a decoded value"*; band is binary), C4 (*"There is no numeric band: `T-WP15` is a named omission"*), C8 (binary set), C9 (negative binary band, no pull) |
| Looks & audio | **3 of 6** | NIGHT pass rule `count == 18` (§2.1); HUD_CHECK "marker within ±6 px of −111" plus six more rows (§3); AUDIO peak > 0.001, four distinct hashes, `mapped=5`, `donor=21/45` (§6.6). Excluded: LOOK_STATIC and LOOK_CLOSEUPS (pass on frames existing and hashes differing), RAIN (its numbers are §5.2 **reviewer** thresholds, not the card's RESULT) |
| Prove-set | **0 of 9** | §2's order table has no band column; §4.1 marks P5/P6 *"not-yet-provable"* and the radius / 0.25 s rows *"not scored at all"* |

The four bands that are **declared, not sourced** and must be read as such: A9's 4.5–7.5 m/s²
(*"no D-row exists for A9"*, `pilot-card-driving-takes.md` §5.5), and the looks pilot thresholds in
`pilot-card-looks-and-audio.md` §0 (2.0–3.0 m, 60/255, ≤12 spread, 8/255, 6 s ±1 s).

## 3. Still `UNKNOWN` for their expected value — 15 of the 34

| area | UNKNOWN | cards, and the file naming each |
|---|---:|---|
| Driving | **4 of 8** | A3 radius, A4 exact 0.25 s, A6 no-bounce, A7 drift angle — `pilot-card-driving-takes.md` §6 verdict table and §7's six-row gap table (the six rows also carry A9's missing D-row and A4's out-of-domain 0.091 s) |
| Combat | **9 of 11** | §9 names six — C1/C2 shots to kill, C2 overheat time, C1/C5 damage & target health, C3 lock duration, C6 mode threshold, C8 marker count; the card bodies add C4 (*"no numeric band"*, `T-WP15` omission), C10 (*"did the flip hold"*), C11 (*"which member the engine reads"*). C7 and C9 carry none |
| Looks & audio | **2 of 6** | LOOK_STATIC `L4` camera *"**`TOP_VIEW` = UNKNOWN**"* (§1) and HUD_CHECK reticle size *"UNKNOWN — no unit map; not scored"* (§3). NIGHT/RAIN/AUDIO/LOOK_CLOSEUPS carry no UNKNOWN band |
| Prove-set | **0 of 9** | the word is used once, for the Serpente spawn **route** (*"`UNKNOWN` in every repo file"*), which is a calibration field, not a band |

A card can be both: 12 of the 34 have a numeric band **and** an UNKNOWN sub-value.

## 4. The review's fix list — `review-pilot-cards.md`

Measured frame the review audited against: **15 blocked rows** (11 ledger + 4 T6), **109 `next`**,
**12 of 23** texture rows unfaithful, **21 of 45** audio GUIDs donor, collision **2 bodies / 3 boxes
with 2 shapes missing**, and all **three stale checkers green** (`v05_driving` 34/34,
`t_boost_rows` 21/21, `t_vnf_six` 87/87). Result: **13 files rewritten in place** (9 cards,
4 card documents) and **7 briefs (86xx)** now name the cards they must follow.

| file | defect found → fix applied |
|---|---|
| `ENTER_EXIT` (**broken**) | step 5 pressed `E` even when `Y` entered (`E` is also `EXIT_VEHICLE`, so it could eject Rico and then score the exit frame as an entry); step 8 copied `enter_y.png` whichever key worked; step 10 heading `LB` vs its `E` command, and `>>` append; "CHECK the frame" was a judgement → step 5 conditioned and warns off `E`; step 8 names its branch; heading matches command, `LB` is an operator press; `>` with `wc -l` = 1 |
| `AIRFIELD` (**broken**) | step 7 printed `max()` of the sample deltas, so a positive gain always satisfied `> -5`: **the check could not fail** → `min()`; pass only when no delta is below −5 km/h |
| `LAUNCH` | step 12 asserted a timing (*"returns after about 120 s"*) no tool reports; no input-layer step → exit 0 only; **new step 19** sends `scanmode on` once |
| `SCREENSHOT` | `<name>` placeholder inside four commands; no branch for a key returning `ok` and changing nothing → literal `shot1`; `scanmode` retry branch |
| `RECORD` | peak reader assumed float32 with no branch; `--offset 0.25` unlabelled → refuses a peak above 1.0 and names the assumption; offset labelled a pilot threshold |
| `KILL` | step 5 used `taskkill //F //PID`, in no cited source → second documented `um win kill <pid>`; a second failure is the zombie, not an escalation |
| `LOAD_SAVE` | step 8 read as unconditional though it applies only when step 7 saw no change → conditioned on step 7's `SEE` |
| `SPAWN_BATMOBILE` | step 6 told the pilot to read `Bring to garage` / `Err: No Valid locking reason` off a PNG (no OCR in the repo) → frame hash is the check; text becomes `observed (human)` |
| `PROVE_CARDS` | §3 claimed `v05_driving.py --check` "is not green" (it is); §4 knew two meanings of B-15 → states the measurement and why green ≠ evidence; B-15's three meanings |
| `pilot-card-looks-and-audio` | `HUD_CHECK` step 2 checked `hud_cannon.png` no step captured; step 4 wrote the verdict with the **expected values pre-filled** (`reticle=8@-111`); `NIGHT` required *"visibly darker"*; `AUDIO` RESULT named `audio/*.mp4` nothing muxed; `close_<target>.png` placeholder → capture added as step 2b; template refuses to submit with a `<...>` left; hash + reviewer crop mean; RESULT names `.mkv` + `.audio.raw`; five literal frames |
| `pilot-card-proving-on-a-simple-car` | reported the checker as *"started and did not finish in 90 s"*; B-15 two meanings → measurement replaces the timeout (exit 0, 34/34); third B-15 meaning |
| `pilot-card-driving-takes` | A2 read a `measure` key (`peak_kmh`) in no repo file; A6 could PASS on "ride height unchanged" from two PNGs with no scale; "3 attempts, 2 clean" under-counted brief 8602's three repeats; an "optional" leg; no stale-checker warning → CSV arithmetic; ride-height clause deleted, A6 ends `UNKNOWN`; 3 clean takes after one calibration; leg 3 is a step; warning paragraph |
| `pilot-card-combat-and-gadgets` | §5 mapped C6 to `WPN-11…13` (booster and slot row, not the mode rows); B-15 named without its path; §6 declared "seven columns" then showed nine → `T-MD5`/`T-MD6`/`T-MD10`/`T-MD11` plus the `T-MD8`/`T-MD14` omissions; B-15's three meanings; seven + two columns |
| `CARD_FORMAT`, `CONTROLS` | none — *"the format held; every defect above is a violation of it"* → unchanged |

The review's three defect classes, which are the rule to apply to any new card: **a step that needs
judgement**, **a command not copied from a source**, **an observable that cannot be read from a
frame**. Its closing rule: *"if a PNG has no scale, no OCR and no gadget that reads the value, the
card records the frame and writes `UNKNOWN` for the number."*

Revert: delete this file; no card, script or build file was touched to produce it.
