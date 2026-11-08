# Emergency mode - first trial, 2026-11-05/06 (JC3-Batmobile, AFK Claude)

Result: **FINAL COUNT PENDING - fill in after 05:00Z** (hours spent / hours expired; see "Outcome" at the bottom).
Operator ruling (in person, 2026-11-06): *If the day's hours are not at 0 at the reset, emergency mode failed.* Claude has FULL AUTHORITY to
spend the remaining daily hours as the operator would; whatever needs "the user" is Claude.

## Hiccups, cause, fix

| # | What happened | Cause | Fix (done unless marked) |
|---|---|---|---|
| 1 | GUI showed no lanes right after the Emergency button was added | A literal newline inside a JS string in `index.html` broke the whole page script | Fixed; **rule: every GUI edit is gated by `node --check` on the extracted script** |
| 2 | Button did nothing / "not active" | `server.py` needs a GUI restart to load `/api/emergency`; the old process kept running | GUI restarted; state API now reports `emergency` and `admin`; button label shows `· admin` / `· NOT admin` |
| 3 | A live session sat idle with ~6 min left (`FILLER POOL EMPTY`) | Queue was empty; templated fillers are off (policy) so nothing could refill it | Briefs must be written BEFORE sessions start; prompt step 0 + queue-depth rule (>= 6 briefs per live lane) |
| 4 | GUI run sat on `HOLD: need N more minutes of work` even with 17 briefs, then "lanes running - waiting" and never added lane 2/3 | `runner()` only starts a batch when no lane is up and `need()` is satisfied; it never adds a lane next to a live one | Emergency loop now starts individual missing lanes (plan counts lanes already up); AFK Claude/`lane_keeper.sh` launch `driver.cjs --parallel 1` directly |
| 5 | ~10 min gaps between sessions (21:50Z, 22:00Z) | Sessions are 60 min; the monitor ran every 12 min and nothing renewed lanes at the exact end | `scratchpad/lane_keeper.sh` pattern: relaunch a lane when its log says `exit`, until 04:58Z; GUI loop does the same in emergency mode |
| 6 | **Freebuff refused a new session's first message at 23:04Z** ("usage policy"); driver wrote `NO_NEW_SESSIONS`; all lanes stopped; **~4 h of hours were not used (23:04Z-03:00Z)** | (a) every brief I wrote ended with the same long rules paragraph (the 2026-11-03 "same job again and again" pattern); (b) several near-identical review briefs; (c) the prompt told Claude NOT to clear the flag, so Claude waited for the operator | (a) shared rules are now a one-line pointer to `INSTRUCTIONS.md`, each brief worded for its task; (b) `too-similar` guard parked 7215/7238 - never queue look-alike reviews together; (c) **prompt rule 3: emergency mode NEVER stays stopped - Claude deletes `NO_NEW_SESSIONS` (and a refusal-written `PAUSED`) itself, parks the refused task (never resend/reword), restarts lanes at once**; GUI emergency loop does the same |
| 7 | Conflicting authority: SKILL.md said the flag is the operator's; the operator wanted autonomy | Policy written for the keeper era, not for emergency mode | SKILL.md emergency section added (below); emergency prompt rewritten |
| 8 | 2 near-duplicate briefs parked, 1 brief (7229) ran 59 min without a report, 1 old task (7123) stuck to lane 3 for a day | Long open-ended briefs; a stale task bound to a lane | Keep briefs to one measurable output (<= 45 min); re-brief hung tasks as a NEW narrower brief, never a resend |
| 9 | Lots of check-ins that only said "no change" | Cron ticked every 12 min while everything was blocked | Step 0 of the loop: if a lane is down and hours remain, FIX IT FIRST; "waiting on operator" is not an allowed status while hours remain |
| 10 | Confusion about hours | `START ... daily=N/53` is the reading BEFORE that session's charge; Flash Normal costs 3 h per 60-min session (Slow 2 h), so 3 lanes spend 9 h per hour-long wave | `model_plan.cjs` already spends the last hours exactly (8 h = N+N+S); the prompt says: renew all 3 lanes at every session end |
| 11 | Second refusal at 04:06Z on lane 3's NEW session (daily=2, Slow model); the session ended seconds later | The first message of the session was `7269-all-checks-sweep-h.txt #2`: the SAME text already sent (#1) in the previous session, resent because that session ended before the task finished (the 23:04Z refusal was also a first message of a fresh session). Resending identical text = Freebuff's "same job again and again" | **Never let a driver resend an unfinished task verbatim.** When a lane's session is about to end with a task unfinished, write a NEW narrower brief for the remainder (different scope/words) and park the old one. The AFK Claude moves the old task out of `queue/` before relaunching a lane, and puts a fresh brief first (lowest file name) so a new session's first message is always new text. The refused task stays parked |
| 12 | After the hours hit 0, `lane_keeper2.sh` relaunched drivers every ~2 min; each exited with `no free hours` but the node processes stayed alive (9 stale `driver.cjs`, some from the previous day) | The keeper only tested the log's last line for `exit`, not whether hours remained; drivers that decline to start do not exit | Keeper must stop when a START reading says `daily=0`; before launching, kill stale `driver.cjs` processes that have no live `freebuff.exe`; probe the reset with ONE driver per check, never a loop |
| 13 | Emergency mode kept going after the hours hit 0 (keeper relaunching, monitor job still firing) | Nothing defined when emergency mode ENDS | **Operator rule: 0 daily hours = emergency mode is over.** GUI loop: `hours_exhausted()` (newest START reading `daily=0`, counting only readings taken after the switch was armed) -> `emerg_end()` switches the switch off and writes `tmp/freebuff/emergency-ended.txt`. `scripts/emergency_keeper.sh <project>` exits itself at `daily=0`. Prompt section "EMERGENCY MODE ENDS AT 0 DAILY HOURS": write summary, switch off, stop keepers, kill stale `driver.cjs`, delete the monitor cron, exit. No reset probing |

## What "automated" means (operator clarification, 2026-11-06)
Freebuff's usage policy ("Automated loop") targets similar, spam-like text sent repeatedly - it does not forbid a dynamic agent. Claude is not posing as
a human; it may write distinct, task-specific text itself. Order of preference: (1) hand-written distinct briefs in the queue (most accurate), (2) a
distinct brief via `say-L<k>.txt` for a refused/MANUAL lane, (3) last resort: Claude types a distinct message itself. Never resend or lightly reword a
refused message, never send look-alike series.

## Checklist for the next emergency
1. Click Emergency in the GUI (page must show `Emergency: ON · admin`). Confirm queue >= 6 briefs per lane BEFORE sessions start.
2. At every check: lanes down + hours left -> clear flags, relaunch lanes first, then everything else.
3. Never queue two similar briefs; never paste the rules paragraph; one output per brief.
4. After 04:00Z make sure every lane has a fresh session (last renewals), then final report. At `daily=0` emergency mode is OVER (automatic in the GUI; use `scripts/emergency_keeper.sh` for the keeper).
5. Always `node --check` the GUI script after editing `index.html`; restart `gui.cmd` after editing `server.py`.

## Outcome (written 05:01Z, 2026-11-06)
* Daily-hour readings at session starts (hours remaining BEFORE that start's charge): 23:03Z 11 (previous wave) ... 03:00Z 14 -> 03:02Z 11 -> 04:02Z 8 -> 04:05Z 5 -> 04:05Z 2 (lane 3, Slow = 2 h).
  After lane 3's Slow session the counter should read **0** (14 - 3x4 - ... exact: 14 -> 11 -> 8 -> 5 -> 2 -> 0). All three lanes ran the final wave to the reset (05:04-05:07Z).
  CONFIRMED: START readings at 05:06Z, 05:08Z and 05:11Z all read `daily=0/53 hours remaining` -> **hours remaining at the end of the run: 0. Emergency mode succeeded in spending every hour.** (Observed: the counter was still 0 at 05:11Z, so the reset time is UNKNOWN; per the operator, emergency mode is simply over at 0 - do not probe.)
* **Hours lost:** the refusal at 23:04Z left all lanes down until 03:00Z (about 4 h of wall time). Those hours were NOT lost in the daily counter - the counter only drops when a session starts, and the full
  remainder (14 h at 03:00Z) was spent before the reset - but the work those 4 h of lanes could have produced was lost, and any day with less slack would have ended with hours unspent.
* Verdict: **partial success** - hours spent down to 0 only because 14 h were still free at 03:00Z. Without the operator's intervention at ~03:00Z, ~14 h would have expired. The fixes above address exactly that.
* Work output: ~45 reports in `JC3-Batmobile/tmp/freebuff/reports/`, ~40 GRAB_BACKLOG tracker rows, new offline trees `Working/Installer/install_v3`, `Builds/bm-RC3-parts`.

## Emergency mode ended 2026-11-06 ~17:00Z
- Daily hours exhausted (last numeric START daily=2/53 at 16:44Z; lanes 2 and 3 refused by WALLET GUARD at 16:48Z, "daily left=null"). Break-glass (wallet hours) NOT used.
- Switched emergency-mode.json off, stopped emergency_keeper.sh, deleted the 15-minute cron (f4b8d9da). Lane 1 finishes its paid session on 8207 (apply-mode-switch-rows, ~46 min left).
- State left: queue ~49 files (apply chain 8207-8216 -> close-out 8250 -> review 8299 -> build 8300-8320 -> verify 8400-8406 -> pilot 8505-8599 -> gated tests 8600-8605 wait on APPROVED_Q.txt). ledger pin t_blocked.py --check PASS (13 blocked rows of 211). Jebadiah judge evaluated: Qwen stays default; smart search route change in 8719 (held), 8734/8707/8008/7204 held in queue/held.
- Next session: re-run after the daily reset (time UNKNOWN, ~05:00Z earlier observed), restart lanes, check held/ and low/too-similar for briefs to rewrite (8752-8763 done; others).
