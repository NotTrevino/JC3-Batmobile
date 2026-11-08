STATUS: done. The repo does contain earlier piloting failures, but they cluster in four places, not seven: the QA-1 driving take (2026-10-22), the test-086 camera take (2026-10-22), the Q-1a entry/spawn chain and Q re-test 4/5 (2026-11-02), and the Q-4 control runs (2026-11-03). **Three of the seven requested categories have no evidence in this repo at all** — lost input focus, window-not-found and zombie process — and are marked NO EVIDENCE rather than filled from the universal-modder notes. Every row below carries the file and line it came from; nothing was re-run (test ban). This is the "known traps" source for every piloting card.

# Pilot failure catalogue

Searched: `MODLOG.md` (20,992 lines; greps listed in §6), `Working/Translation/QA1_RESULTS.md`, `Working/Q/` (only `PREDICTIONS*.md` and `predictions.json` exist — no pilot notes yet), `tmp/freebuff/reports/` (names and the relevant files), `tmp/freebuff/queue/8502..8605` (the pilot briefs, which cite the lessons, not the failures). Nothing was launched.

## 1. The failures, by category

### 1.1 Vehicle entry — FAILED TWICE, then fixed

| # | symptom (exact, as recorded) | date | evidence | fix |
|---|---|---|---|---|
| E-1 | "**unenterable**" — the drop delivered the car, the agent could not get in. First Batmobile hull on its own wheels. | 2026-11-02 | `MODLOG.md:19879` (Q re-test 4 result) | T-13 anchored "every point/trigger 0.05–0.30 m off the body shell": unit scale instead of the donor trigger half-extents, invented 90°/180° yaws, 8 points collapsed onto 3 anchors, seat point "outside on the cockpit wall at y 1.15". |
| E-2 | after the fix: "**entered**, collision still misalign" | 2026-11-02 | `MODLOG.md:19940` (Q re-test 5) | **T-13R works**: trigger half-extents 3.48 x 2.85 x 3.91 m at (-1.94, -0.08, -0.93); `point.driver.onground` (-1.747, 0.091, -0.266) "beside the cockpit"; enter **from the left**, beside the cockpit. |
| E-3 | car **not obtainable at all**: entry "LOCKED"; then "Err: No Valid locking reason"; then the drop delivered nothing (twice, with vanilla bytes and with the RC `.ee`). | 2026-11-02 | `MODLOG.md:19661` (re-test 2), `:19670` (empty drop probe), `:19700` (new leaf never spawns), `:19721` (re-test 3) | entry = starter reward on task 1980624442; spawn = a `spawn_vehicle_defs.bin` record, not a new entity path. Re-test 3 PASS ("it drops"). |

Pilot trap: **a listed vehicle is not a spawnable vehicle**, and a spawned vehicle is not an enterable one. Three separate links (item → defs record → interaction volume).

### 1.2 Driving the take — the car left the road; no controlled input

| # | symptom | date | evidence | fix |
|---|---|---|---|---|
| D-1 | "The car left the road at ~106 km/h around t=203 and stopped in vegetation (64→0 in 1.2 s is an impact)." 100→0 on tarmac **not captured**; kerb, ride height, 60 km/h corner untested. | 2026-10-22, recorded 17:42:44–17:52:44 | `Working/Translation/QA1_RESULTS.md` §4 and §5; `MODLOG.md:6741` | none needed in the car — the take was one continuous free run from standstill to 138 km/h. **Fix is procedural**: one prescribed manoeuvre per take (`QA1_RESULTS.md` §7: "one manoeuvre per take (§9)"; "**re-take**; the data is never reinterpreted"). |
| D-2 | take peaked at **103 km/h** when the gate was 300 km/h; "the 300 km/h gate was not reached" | 2026-10-22 | `MODLOG.md:6898-6899` | re-take with a longer straight; nothing in the build changed. |

### 1.3 Camera — "less zoomed in" was a unit error, not taste

| # | symptom | date | evidence | fix |
|---|---|---|---|---|
| C-1 | player verdict after the driving take: "**less zoomed in** — the car reads small/far compared with the target view." | 2026-10-22 | `MODLOG.md:6901-6903` | first treated as tuning (FOV/distance knobs); later proved a **conversion bug** (C-2). |
| C-2 | BmAK FOV 85/95 is UE3 **horizontal**; copied into JC3's **vertical** `FOV` it is ~114° horizontal at boost. The camera distance had been hand-derived as a 7.0 m boom from body length. | 2026-10-22 (G3d) | `MODLOG.md:6925-6945` | convert `v = 2·atan(tan(h/2)/(16/9))`: **85→54.5°, 95→63.1°**, top 68.4° with the +10 bonus; range 55…63, not 55…85. The real distance was in the grab all along: `DrivingCamConfig1/2` carry **400/400 cm** — the earlier read had used `DrivingCamConfig`, a zeroed template. **test-086 withdrawn.** |
| C-3 | "a per-entity camera reference is the missing piece" — that conclusion "was wrong" | 2026-10-22 | `MODLOG.md:6842` | decoded the ctunec routing instead (`bat_base.ctunec` registered per entity; 12/12 checks). |

Pilot trap: **do not judge "too far/too close" from one screenshot** — check the unit first (JC3 `FOV` is vertical) and the source record (`DrivingCamConfig1/2`, not `DrivingCamConfig`).

### 1.4 Wrong key / control confusion — the binding table was wrong twice

| # | symptom | date | evidence | fix |
|---|---|---|---|---|
| K-1 | user's own spec, believed at the time: "LT switches to battle mode… B tracks enemy or fires immobilizer missile… LB exits, A: electromagnetic ejection." | 2026-11-02 | `MODLOG.md:20058` | decoded against `DefaultInput.ini`: **none of these is a named Batmobile command**; the meaning lives in the driving-state script, not the config. Recorded as `stated (user)`. |
| K-2 | **5/5 user statements UNKNOWN from the script**; LB has no script reader; `ToggleBattleMode` has no script call site; LT is stored to `LastTriggerAmount` only. | 2026-11-02 → 2026-11-03 | `MODLOG.md:20142` (G3-02b), `MODLOG.md:20160` (G3-02c) | native side located the mode switch (`ARPlayerController.DrivingPlayerMove`, `TryToChangeMode` calls at 0x140255f5e/0x140255fc5), but the input→state link stays UNKNOWN. **Do not write a card that claims a decoded binding.** |
| K-3 | user correction after watching the run: "**it was X not B. Y is boost in pursuit** btw. I rammed into a drone after using missile barrage." Six B presses in battle changed no weapon/target field. | 2026-11-03 (run 6) | `MODLOG.md:20480-20502` and `:20502` | X = barrage (`SelectVehicleWeapon(2)`), B = `SelectVehicleWeapon(1)`, Y = boost (`bVehicleBoostButton`, ini line 270). |
| K-4 | "tracking" was assumed to be a B action; the log shows targets are **tagged automatically when in range** (11:53:43.969, no input). B press at 52.036 produced the lock (LockOnTime 0.076→0.383 in ~0.31 s) and launch at 52.851. | 2026-11-03 (run 5) | `MODLOG.md:20485-20490` | statement 2 confirmed, "tracking" corrected; statement 3 (B in battle = barrage) never confirmed — it is X. |
| K-5 | a key press left **no runtime trace** because the fields were not sampled: "X and RBatmobileMissileLauncher were not sampled -> the barrage left no runtime trace." | 2026-11-03 | `MODLOG.md:20500` | add the input and the weapon-launcher fields to the sampler before concluding "the key did nothing". |
| K-6 | required behaviour is a **switch on entry**: "it should enter with JC3 control, but once in switch to lore controls"; later "only ENTER with JC3 controls (exit and else with BmAK controls)". | 2026-11-02 | `MODLOG.md:19880`, `:19908`, `:19912` | D-11; the switch itself is a build item, not a pilot step. |

### 1.5 Lost audio channel — real, and it was a flag

| # | symptom | date | evidence | fix |
|---|---|---|---|---|
| A-1 | the take has **no audio at all**, so JC3's only rpm channel was missing and the gearbox cross-check stayed partial: "a full shift-point check needs an engine-rpm channel, and JC3's only one is audio, which this take does not have (`um win record --no-audio`)." | 2026-10-22 | `Working/Translation/QA1_RESULTS.md` §3; `MODLOG.md:6748` | record with audio. Already a pipeline rule: the RECORD card is specified "with audio, per the QA-1 lesson" (`tmp/freebuff/queue/8503-pilot-card-format-and-launch.txt`). |

Not the same failure as a muted process (that upstream trap records exact silence); here the audio was never captured.

### 1.6 Launch / window / recording

| # | symptom | date | evidence | fix |
|---|---|---|---|---|
| L-1 | "The first recording attempt **died with the game before the menu**; a relaunch + `um win record` captured the run." | 2026-10-22 | `MODLOG.md:6899-6900` | separate launch from record; relaunch, then start the capture. The card must have this step. |
| L-2 | load crashes during the Q-1a/Q re-test chain: `ACCESS_VIOLATION READ 0x8 at JustCause3.exe+0x2d49e0`, then `READ 0x60 at +0x14fbac1`, then `READ 0xFFFFFFFFFFFFFFFF at +0x151410f`. Each **new signature meant the previous cause was fixed**; dumps are named `JustCause3.exe.<pid>.dmp` under `%LOCALAPPDATA%/CrashDumps/`. | 2026-11-02 05:10–06:34 | `MODLOG.md:19916` (dump .16236), `:19930` (.14112/.14412), `:19940` (.14384), `:19866` (.7584) | read the signature before re-litigating: `+0x2d49e0` = parts-module schema; `+0x14fbac1` = per-part physics body with a null owner; `+0x151410f` = a node with a raycast handle whose body slot has no shape (the 4 arch lamps parented under wheel parts). |
| L-3 | Lost input focus, window not found | — | **NO EVIDENCE in this repo.** Greps for `focus`, `foreground`, `window not found`, `alt-tab`, `minimize` over `MODLOG.md` return only unrelated hits (window = glass, camera naming). | upstream-only risk; the pilot-study report §2/§6 carries the rules (`idle` check, Alt-tap before focus, one launch per boot). Do not present it as observed here. |
| L-4 | Zombie process (windowless, one-thread, unkillable by PID) | — | **NO EVIDENCE in this repo.** No entry mentions a PID that survived `taskkill`/`Stop-Process`, and no reboot request. | upstream-only (`knowledge/techniques/a-force-quit-pc-game-relaunch-wedges-as-an-unkillable-zombie.md`). The card still needs the check, but as a precaution, not a repo lesson. |

### 1.7 Reading values — the HUD instrument lied twice before it was trusted

| # | symptom | date | evidence | fix |
|---|---|---|---|---|
| R-1 | band included the `KM/H` legend, so K/M/H strokes fed the first digit: **3 read as 5, 0 as 9, 8 as 5**. | 2026-10-22 | `MODLOG.md:6736-6738` | crop the legend out; digits that touch are split by the **42 px digit pitch**, not by column runs. |
| R-2 | digits touching made column runs useless | 2026-10-22 | same | as above; `build` refuses to trace until every glyph in the take has a label, "so an unseen digit fails loudly instead of producing a number" (`QA1_RESULTS.md` §1). |

Pilot trap: any value read off the HUD must be validated against a frame a human read (`QA1/known.json`, 22 frames) before the take is trusted.

## 2. What the pilot could not test at all (so a card must not claim it)

`QA1_RESULTS.md` §5: T-M2/T-M3 (yaw response, balance: "no controlled steering input"), T-S1/S2/M4 (kerb, pothole, landing), T-G5 (low-speed grip), T-LG*/T-AU*/T-FX*/T-DM* (night beams, pitch, window break, pursuit) — not tested. §7: the five queued takes (A2 top speed, A5 braking, A9 boost, A7 drift, A6/A8) were written down and **never driven** ("Nothing below has been driven"). T-5 is "built + launch measured", not verified (`MODLOG.md:6747`).

## 3. The "known traps" block for the cards (ready to paste)

1. **One question per take.** A free drive ends off the road (D-1). Script the manoeuvre, state the exit condition, re-take rather than reinterpret.
2. **Record with audio, always.** `--no-audio` deleted JC3's only rpm channel (A-1).
3. **JC3 `FOV` is vertical.** BmAK's 85/95 are horizontal: convert before judging zoom (C-2). Camera distance lives in `DrivingCamConfig1/2` (400/400 cm), never hand-derive it (C-2).
4. **Entry is a volume, not a point.** Trigger half-extents 3.48 x 2.85 x 3.91 m, `point.driver.onground` beside the cockpit; approach from the left (E-1/E-2).
5. **A listed vehicle is not spawnable; a spawned vehicle is not enterable.** Check the `spawn_vehicle_defs` record and the interaction trigger separately (E-3).
6. **Do not trust a binding name.** LT/LB/A exist only natively; B is `SelectVehicleWeapon(1)`, X is the barrage, Y is boost in pursuit — and the user's spec is `stated (user)`, not decoded (K-1..K-4).
7. **Sample the field before concluding "nothing happened".** X and the missile launcher were unsampled, so the barrage left no trace (K-5).
8. **Launch, then record.** The first attempt died before the menu; relaunch and capture (L-1).
9. **Read the dump signature first.** A new `JustCause3.exe+0x…` means the previous fix worked, not that the new build is worse (L-2).
10. **Validate the readout.** HUD OCR misread 3/0/8 until the legend was cropped and digits split by pitch (R-1/R-2).
11. **Focus/window/zombie are upstream risks here, not repo lessons** (L-3/L-4): check `um win drive --proc <game> idle`, never focus while the human types, and assume one launch per boot — but do not cite repo evidence for them.

## 4. Category verdicts (the seven asked for)

| category | evidence in repo? | strongest row |
|---|---|---|
| lost input focus | **no** | L-3 (NO EVIDENCE) |
| wrong key | **yes** | K-3 (X vs B), K-2 (5/5 statements UNKNOWN) |
| camera confusion | **yes** | C-1 → C-2 (vertical/horizontal FOV, wrong config record) |
| vehicle entry | **yes** | E-1 unenterable → E-2 entered; E-3 spawn |
| lost audio channel | **yes** | A-1 (`--no-audio`) |
| window not found | **no** | L-3 (NO EVIDENCE); closest is L-1 |
| zombie process | **no** | L-4 (NO EVIDENCE) |

## 5. UNKNOWNs

1. **Whether any of these still reproduce.** The three fixed ones (entry, camera, spawn) were fixed in builds that were never re-run after the 2026-11-02 research reset; the test ban stands. Would be found by Q-0/Q-1 on a stock car, then the Batmobile.
2. **Which input actually drives the mode switch.** G3-02c reached the native call site and the vehicle flag bits (0x10 / 0x8000 at `[vehicle+0x11d8]`, meaning UNKNOWN) but not the trigger link; a read-only BmAK runtime observation (card G3-02d) would settle it.
3. **Whether a pilot failure was hidden inside a "mod" failure.** L-2's crashes were build faults; no log in the repo distinguishes a *piloting* mistake from a *build* fault in the same session except by the dump signature. A per-step observation log (the Q-0 `PROVE_LOG.md`) is the missing instrument.
4. **The focus/window/zombie categories.** No repo evidence; upstream knowledge exists but is not JC3-specific and is not a decode. Listed as precaution, not as fact.

## 6. Commands run (verbatim, abbreviated to the ones that produced the rows)

```text
$ grep -n -i "Q re-test\|QA-1\|Q-1\|QA1" MODLOG.md
6727:## QA-1 take 1 — the HUD becomes an instrument (2026-10-22, evening)
19661:### 2026-11-02 — Q-1a re-test 2: "Err: No Valid locking reason" -> starter grant
19721:### 2026-11-02 — Q-1a re-test 3: B-13c PASS (it drops); what arrives is a Serpente/Batmobile mix
19866:### 2026-11-02 — probe 8 result: LOADS -> arches-under-wheels confirmed; full own-path build (Q re-test 4)
19879:### 2026-11-02 — Q re-test 4 result: LOADS, Batmobile hull visible; unenterable; collision misaligned -> T-13R
19940:### 2026-11-02 — Q re-test 5 result: ENTERED (T-13R works); collision still misaligned -> B-10c world hull
19959:- User after Q re-test 5 ... "we're back to guess -> test; instead of ...

$ grep -n -i "um win|recorded|recording|take [0-9]|the take|footage" MODLOG.md
6896:**The drive.** Recorded at 1280x720 (`Working/Camera/shots/cam1_take1.mkv`, 90 s) from the main menu
6898:... The first recording attempt died with the game before the menu; a relaunch + `um win record`
6901:**What is still open.** The player's verdict was "**less zoomed in**" ...

$ grep -n -i "control|steer|camera|enter the|entering|keyboard|button|bind" MODLOG.md | grep -iE "user|difficult|hard|wrong|could not|fail|issue|problem|confus"
19880:- User: "loads. [screenshot] unenterable. collision misaligned. Also it should enter with JC3 control, but
20502:- USER CORRECTIONS to the controls spec: barrage = X (not B); Y = boost in pursuit.
```

Files read for this catalogue: `MODLOG.md` (lines 6727-6750, 6880-6945, 19640-20000, 20040-20160, 20460-20520), `Working/Translation/QA1_RESULTS.md` (all), `tmp/freebuff/reports/DRIVERLEFT-regions.md` (checked, not a pilot failure), `tmp/freebuff/reports/jeb-*.md` (checked, LLM judge calibration, not piloting), queue 8502/8503/8599/8600/8601/8602/8603.
