# Instructions for a Freebuff agent working on the JC3 Batmobile project

You were pointed at this file by the operator. Read all of it, then work. Do not reply in chat until your task is
complete: no questions, no confirmations, no progress check-ins. Work autonomously to completion.

## 1. Find your task (claim exactly one) - ONLY if your message did not already give you a task
If your message is a task brief (it names a DONE report path), that is your task: skip this section and section 2,
and follow section 3 and the brief. Otherwise:
1. List `E:/Modding/JustCause3/JC3-Batmobile/tmp/freebuff/manual/` (files ending `.txt`, not the subfolders).
2. Take the **first file in name order** and claim it by **moving** it into `manual/claimed/`. If the move fails
   (someone else took it), take the next file. Never work on a file you did not move yourself.
3. If no `.txt` file is left, reply exactly `NO TASK LEFT` and stop.

## 2. Read the task file
- `DONE: <path>` is the report you must write. The task is complete only when that file exists.
- `ONLY:`, `EST:` and `NEEDS:` lines are bookkeeping; ignore them.
- Everything else is the task: its goal, files to read, outputs and rules. Its rules are in addition to section 3.

## 3. Project rules (all tasks)
- **Translation and build are allowed (operator, 2026-11-05).** Build into NEW private trees under `Builds/` and `Working/` (never edit an existing `Builds/bm-*` tree). Goal: 100% BmAK lore accuracy; a JC3 limit is amended, never accepted silently. List any compromise from lore accuracy in your report under `COMPROMISES` with the reason, because the operator has to approve it.
- **In-game testing (operator, 2026-11-08) is allowed ONLY in a brief whose `AFTER:` line names `APPROVED_Q.txt` or `APPROVED_Q_FULL.txt`.** Every other brief keeps the test ban: no install scripts, no writing under a game install or dropzone, no launching or attaching to a game.
- **In-game briefs run UNATTENDED.** The operator is not watching and only spot-checks now and then. This rule overrides any brief text that says the operator supervises, is present, or takes control.
  - Use only the pilot cards (`Working/Q/PILOT/`, `Working/Q/PILOT2/` when present) and the hook telemetry, never improvised input.
  - Back up saves first (`um backup`). Install only with the brief's `install_v3` receipt, and undo with that receipt afterwards. Kill the game only by exact PID (KILL card).
  - Change one variable per launch, unless the brief batches checks that cannot interact.
  - Never wait for a human. If a step needs one (a UAC prompt, an unknown menu, a crash loop, a calibration value marked UNKNOWN, an observation you cannot judge from screenshots or telemetry), add one line to `tmp/freebuff/NEEDS_OPERATOR.md` in the form `- [ ] <UTC time> <brief file>: <what is needed> (<evidence path>)`. Then stop that check, finish the rest of the brief, and mark the check NEEDS-OPERATOR in the report.
  - Leave the game closed and the dropzone restored when you finish.
- **The one rule: never guess.** Label every value **decoded** (file + offset/line, or package + export + offset),
  **derived** (rule + inputs) or **UNKNOWN** (what you tried, where it would be found). Never fill a gap from general
  knowledge of Batman: Arkham Knight, Unreal Engine 3 or Just Cause 3. A hypothesis counts only if it is proven
  against the files with an oracle (a check that would fail if it were wrong).
- **Read-only inputs:** the game installs (`E:/Games/...`, `D:/Games/...`), `E:/Modding/_shared/gamedata/` and every file
  another task wrote. Never run, inject into or attach to a game process, except in an approved in-game brief (above).
- **Your outputs:** a NEW script under `Tools/scripts/` with `--write` / `--check` (the check recomputes every number
  from the source bytes), its generated `.md`/`.json` under `Research/` or `Working/`, and the DONE report. Never edit
  another task's files; write a new version instead (`...2.py`).
- Scratch files go in `E:/Modding/JustCause3/JC3-Batmobile/tmp/freebuff/scratch/`. Python: `uv run --with <deps> python ...`.
- No secrets, no network uploads, no git commits, no PRs.

## 4. The DONE report
Write it at the `DONE:` path with:
- `STATUS:` done | partial | blocked, in one line, then a summary;
- the files you wrote;
- every command you ran for the result and its output, verbatim;
- `UNKNOWNs`: each with what you tried and why it is still unknown.

## 5. Finish
1. Run your script's `--check` one last time; it must pass.
2. Move your task file from `manual/claimed/` to `manual/done/`.
3. Only now reply in chat, in one line: `DONE <task file name> -> <report path>`.

## Operator rule 2026-11-06: lore accuracy only
The goal is a 100% lore-accurate BmAK Batmobile in JC3. "JC3 has no system", "keep the donor value", "omit" and "accept the limit" are never a final answer: report a carrier with evidence, or write the exact missing capability as a new card. Do not propose a compromise. Label every claim decoded / derived / UNKNOWN.
Queue headers: `AFTER: <report path>[, <path>]` holds a task until those files exist (dependency order). Gated tests wait for `tmp/freebuff/APPROVED_Q.txt` (Q-0 and the L0 probes) or `APPROVED_Q_FULL.txt` (the whole campaign); both are operator approvals for UNATTENDED agent piloting. The queue map is `tmp/freebuff/QUEUE_MAP.md`.
Closest-system rule (operator 2026-11-06): "JC3 has no system" is never an answer. Name the closest JC3 system (member paths, values, evidence) and the gap; the BUILD stage composes or authors the rest. Stage definitions: STAGES.md at the repo root.
Operator priorities (weapon ranking, HUD leads, leads on open rows): OPERATOR_PRIORITIES.md at the repo root. Weapon work follows that ranking.
